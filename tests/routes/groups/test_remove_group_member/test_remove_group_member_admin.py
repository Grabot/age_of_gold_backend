"""Test for remove group member endpoint when removing an admin."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.sql.selectable import Select

from src.api.api_v1.friends import add_friend, respond_friend_request
from src.api.api_v1.groups import create_group, remove_group_member
from src.models.chat import Chat
from tests.conftest import add_token, add_user
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_remove_group_member_admin_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test removing an admin from a group via direct function call."""
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
        name="Test Group",
        description="A test group",
        colour="#FF5733",
        friend_ids=[friend1.id],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    chat_id = create_response["data"]

    # Make friend1 an admin
    chat_statement_admin: Select = select(Chat).where(Chat.id == chat_id)
    chat_result_admin = await test_db.execute(chat_statement_admin)
    chat_entry_admin = chat_result_admin.first()
    assert chat_entry_admin is not None
    chat_admin: Chat = chat_entry_admin.Chat
    chat_admin.user_admin_ids.append(friend1.id)
    test_db.add(chat_admin)
    await test_db.commit()

    # Admin removes friend1 (who is also an admin)
    remove_request = remove_group_member.RemoveGroupMemberRequest(
        chat_id=chat_id, user_remove_id=friend1.id
    )

    with patch(
        "src.api.api_v1.groups.remove_group_member.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await remove_group_member.remove_group_member(
            remove_request, admin_auth, test_db
        )

    assert response["success"] is True
    mock_emit.assert_awaited()

    # Verify friend1 is no longer an admin
    chat_statement_verify: Select = select(Chat).where(Chat.id == chat_id)
    chat_result_verify = await test_db.execute(chat_statement_verify)
    chat_entry_verify = chat_result_verify.first()
    assert chat_entry_verify is not None
    chat_verify: Chat = chat_entry_verify.Chat
    assert friend1.id not in chat_verify.user_admin_ids
