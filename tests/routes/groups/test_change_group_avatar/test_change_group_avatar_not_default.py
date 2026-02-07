"""Test for change group avatar endpoint when avatar is not default."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.sql.selectable import Select
from fastapi.testclient import TestClient

from src.api.api_v1.friends import add_friend, respond_friend_request
from src.api.api_v1.groups import change_group_avatar, create_group
from src.models.chat import Chat
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_change_group_avatar_not_default_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test changing group avatar when it's not a default avatar via direct function call."""
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

    group_id = create_response["data"]

    # Manually set default_avatar to False
    chat_statement: Select = select(Chat).where(Chat.id == group_id)
    chat_result = await test_db.execute(chat_statement)
    chat_entry = chat_result.first()
    assert chat_entry is not None
    chat = chat_entry.Chat
    chat.default_avatar = False
    test_db.add(chat)
    await test_db.commit()

    # Create mock request with avatar
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()
    mock_request.app.state.cipher.encrypt = MagicMock(
        return_value=b"fake_encrypted_data"
    )

    # Create mock avatar
    mock_avatar = MagicMock()
    mock_avatar.size = 1000
    mock_avatar.filename = "test.png"
    mock_avatar.read = AsyncMock(return_value=b"fake_image_data")

    # Change avatar (should not set default_avatar to False since it's already False)
    with patch(
        "src.api.api_v1.groups.change_group_avatar.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await change_group_avatar.change_group_avatar(
            mock_request, group_id, mock_avatar, admin_auth, test_db
        )

    assert response["success"] is True
    mock_emit.assert_awaited()

    # Verify default_avatar is still False
    chat_statement_verify: Select = select(Chat).where(Chat.id == group_id)
    chat_result_verify = await test_db.execute(chat_statement_verify)
    chat_entry_verify = chat_result_verify.first()
    assert chat_entry_verify is not None
    chat_verify: Chat = chat_entry_verify.Chat
    assert chat_verify.default_avatar is False
