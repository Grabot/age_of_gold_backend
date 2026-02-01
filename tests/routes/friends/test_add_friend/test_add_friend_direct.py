"""Test for add friend endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import add_friend
from src.models.user import User
from src.models.user_token import UserToken
from src.util.util import get_random_colour
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_add_friend_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful add friend via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser1", 1001, test_db)
    assert other_user.id is not None
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)

    # Mock the socket emit
    with patch(
        "src.api.api_v1.friends.add_friend.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response["success"] is True

    # Assert the socket emit was called
    mock_emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_friend_self_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test add friend with self via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    add_friend_request = add_friend.AddFriendRequest(user_id=test_user.id)

    with pytest.raises(HTTPException) as exc_info:
        await add_friend.add_friend(add_friend_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "You can't add yourself"


@pytest.mark.asyncio
async def test_add_friend_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test add friend with non-existent user via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    add_friend_request = add_friend.AddFriendRequest(user_id=999999)

    with pytest.raises(HTTPException) as exc_info:
        await add_friend.add_friend(add_friend_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "No user found."


@pytest.mark.asyncio
async def test_add_friend_already_friends_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test add friend with already friends via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
    assert other_user.id is not None
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)

    # First add friend request
    response1 = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response1["success"] is True

    # Second add friend request (should fail)
    with pytest.raises(HTTPException) as exc_info:
        await add_friend.add_friend(add_friend_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "You are already friends"


@pytest.mark.asyncio
async def test_user_id_is_not_filled(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful change username via direct function call."""
    test_user = User(
        id=None,
        username="test_user",
        email_hash="email_hash",
        password_hash="password_hash",
        salt="salt",
        origin=0,
        colour=get_random_colour(),
    )
    test_token = UserToken(
        id=None,
        user_id=1,
        access_token="access_token",
        token_expiration=0,
        refresh_token="refresh_token",
        refresh_token_expiration=0,
    )
    auth: Tuple[User, UserToken] = (test_user, test_token)

    add_friend_request = add_friend.AddFriendRequest(user_id=1)

    with pytest.raises(HTTPException) as exc_info:
        await add_friend.add_friend(add_friend_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Can't find user"
