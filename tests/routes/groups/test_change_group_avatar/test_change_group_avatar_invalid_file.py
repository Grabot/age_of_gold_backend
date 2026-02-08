"""Test for change group avatar endpoint with invalid file."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from src.api.api_v1.friends import add_friend, respond_friend_request
from src.api.api_v1.groups import change_group_avatar, create_group
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_change_group_avatar_invalid_file_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test changing group avatar with invalid file via direct function call."""
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

    # Create mock request with invalid avatar
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Create mock avatar with no size
    mock_avatar = MagicMock()
    mock_avatar.size = None
    mock_avatar.filename = None

    # Try to change avatar with invalid file
    with pytest.raises(HTTPException) as exc_info:
        await change_group_avatar.change_group_avatar(
            mock_request, chat_id, mock_avatar, admin_auth, test_db
        )

    assert exc_info.value.status_code == 400
    assert "Invalid avatar file" in exc_info.value.detail
