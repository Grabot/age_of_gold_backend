"""Test for remove friend endpoint via direct function call."""

from typing import Tuple

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import remove_friend, add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from src.util.util import get_random_colour
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_remove_friend_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful remove friend via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None
    other_user = await add_user("testuser2", 1002, test_db)
    assert other_user.id is not None
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    other_auth: Tuple[User, UserToken] = (other_user, other_user_token)

    # First add friend request
    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)
    response1 = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response1["success"] is True

    # Accept the friend request from the other user's perspective
    respond_friend_request_request = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    response2 = await respond_friend_request.respond_friend_request(
        respond_friend_request_request, other_auth, test_db
    )

    assert response2["success"] is True

    # Remove the friend
    remove_friend_request = remove_friend.RemoveFriendRequest(friend_id=other_user.id)
    response3 = await remove_friend.remove_friend(remove_friend_request, auth, test_db)

    assert response3["success"] is True


@pytest.mark.asyncio
async def test_remove_friend_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test remove friend with non-existent friend via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    remove_friend_request = remove_friend.RemoveFriendRequest(friend_id=999999)

    with pytest.raises(HTTPException) as exc_info:
        await remove_friend.remove_friend(remove_friend_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Friend request not found"


@pytest.mark.asyncio
async def test_remove_friend_not_accepted_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test remove friend with non-accepted friend via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser3", 1003, test_db)
    assert other_user.id is not None
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Add friend request but don't accept it
    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)
    response1 = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response1["success"] is True

    # Try to remove the friend (should fail)
    remove_friend_request = remove_friend.RemoveFriendRequest(friend_id=other_user.id)

    with pytest.raises(HTTPException) as exc_info:
        await remove_friend.remove_friend(remove_friend_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Can only remove accepted friends"


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

    remove_friend_request = remove_friend.RemoveFriendRequest(friend_id=1)
    with pytest.raises(HTTPException) as exc_info:
        await remove_friend.remove_friend(remove_friend_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Can't find user"
