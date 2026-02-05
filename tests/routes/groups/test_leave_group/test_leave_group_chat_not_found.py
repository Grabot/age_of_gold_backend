"""Test for leave group endpoint when chat is not found."""

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.sql.selectable import Select

from src.api.api_v1.groups import create_group, leave_group
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.chat import Chat
from src.models.group import Group
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_leave_group_chat_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test leaving a group when chat is not found via direct function call."""
    from unittest.mock import AsyncMock, patch

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

    # Manually delete the chat to simulate chat not found
    chat_statement: Select = select(Chat).where(Chat.id == group_id)
    chat_result = await test_db.execute(chat_statement)
    chat_entry = chat_result.first()
    # First delete the group entries that reference this chat
    group_statement: Select = select(Group).where(Group.group_id == group_id)
    group_result = await test_db.execute(group_statement)
    group_entries = group_result.scalars().all()
    for group_entry in group_entries:
        await test_db.delete(group_entry)

    # Now delete the chat
    await test_db.delete(chat_entry.Chat)
    await test_db.commit()

    # Recreate a group entry for admin_user to simulate the edge case
    # where group entry exists but chat doesn't
    group_entry = Group(
        user_id=admin_user.id,
        group_id=group_id,
        unread_messages=0,
        mute=False,
        last_message_read_id=0,
    )
    test_db.add(group_entry)
    await test_db.commit()

    # Try to leave group - should fail with chat not found
    leave_request = leave_group.LeaveGroupRequest(group_id=group_id)

    with pytest.raises(HTTPException) as exc_info:
        await leave_group.leave_group(leave_request, admin_auth, test_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Leaving group failed" in exc_info.value.detail
