"""Test for change username endpoint via direct function call."""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.api.api_v1.settings import change_username
from src.models.user import User
from src.models.friend import Friend
from src.models.user_token import UserToken
from src.util.util import get_user_room
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_change_username_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful change username via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    test_user_username = test_user.username
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    new_username = "new_username"
    change_username_request = change_username.ChangeUsernameRequest(
        new_username=new_username
    )
    response_json: dict[str, Any] = await change_username.change_username(
        change_username_request, auth, test_db
    )

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.id == test_user_id
    assert test_user_result.username != test_user_username
    assert test_user_result.username == new_username


@pytest.mark.asyncio
async def test_change_username_updates_friend_versions(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test that changing username updates friend versions and emits socket events."""
    # Setup: Add a friend for the test user
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    friend_user = User(
        id=2000,
        username="friend_user",
        email_hash="test@example.com",
        password_hash="hashedpassword",
        salt="salt",
        origin=0,
    )
    test_db.add(friend_user)
    await test_db.commit()
    await test_db.refresh(friend_user)

    # Add a friend relationship
    friend = Friend(user_id=friend_user.id, friend_id=test_user.id, friend_version=0)
    test_db.add(friend)
    await test_db.commit()

    # Mock the socket emit
    with patch("src.api.api_v1.settings.change_username.sio.emit", new_callable=AsyncMock) as mock_emit:
        # Call the function
        new_username = "new_username"
        change_username_request = change_username.ChangeUsernameRequest(
            new_username=new_username
        )
        auth = (test_user, test_user_token)
        response_json = await change_username.change_username(
            change_username_request, auth, test_db
        )

        # Assert the response
        assert response_json["success"]

        # Assert the friend_version was incremented
        friend_result = await test_db.get(Friend, friend.id)
        assert friend_result is not None
        assert friend_result.friend_version == 1

        # Assert the socket emit was called
        mock_emit.assert_awaited_once_with(
            "username_updated",
            {
                "user_id": test_user.id,
                "new_username": new_username,
                "profile_version": test_user.profile_version,
            },
            room=get_user_room(friend.user_id)
        )
