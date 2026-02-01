"""Test for leave group endpoint empty notification loop."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.friends import add_friend, respond_friend_request
from src.api.api_v1.groups import create_group, leave_group
from src.models.chat import Chat
from src.models.group import Group
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_leave_group_empty_notification_loop_direct(
    test_setup: any, test_db: AsyncSession
) -> None:
    """Test leaving group with empty notification loop via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    # Create friend
    friend1 = await add_user("friend1", 1001, test_db)
    assert friend1.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_auth = (admin_user, admin_token)
    friend1_auth = (friend1, friend1_token)

    # Add and accept friend
    add_request = add_friend.AddFriendRequest(user_id=friend1.id)
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await add_friend.add_friend(add_request, admin_auth, test_db)

    respond_request = respond_friend_request.RespondFriendRequest(
        friend_id=admin_user.id, accept=True
    )
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        await respond_friend_request.respond_friend_request(
            respond_request, friend1_auth, test_db
        )

    # Create group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[friend1.id],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    group_id = create_response["data"]

    # Manually remove friend1 from the group first, leaving only admin
    chat_statement = select(Chat).where(Chat.id == group_id)
    chat_result = await test_db.execute(chat_statement)
    chat_entry = chat_result.first()
    assert chat_entry is not None
    chat = chat_entry.Chat

    # Remove friend1 from user_ids, leaving only admin
    chat.user_ids = [admin_user.id]

    # Also remove friend1 from group entries to maintain consistency
    group_statement = select(Group).where(
        Group.user_id == friend1.id, Group.group_id == group_id
    )
    group_result = await test_db.execute(group_statement)
    group_entry = group_result.first()
    if group_entry:
        await test_db.delete(group_entry.Group)

    test_db.add(chat)
    await test_db.commit()

    # Admin leaves group (should trigger empty notification loop)
    leave_request = leave_group.LeaveGroupRequest(group_id=group_id)

    with patch(
        "src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await leave_group.leave_group(leave_request, admin_auth, test_db)

    assert response["success"] is True
    # Should not emit any notifications since user_ids was [admin_user.id] and we filter out self
    mock_emit.assert_not_awaited()
