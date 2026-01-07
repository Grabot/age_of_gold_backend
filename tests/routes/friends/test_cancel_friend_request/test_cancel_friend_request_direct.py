"""Test for cancel friend request endpoint via direct function call."""

from typing import Tuple

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import (
    cancel_friend_request,
    add_friend,
    respond_friend_request,
)
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_cancel_friend_request_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful cancel friend request via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
    assert other_user.id is not None
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Add friend request
    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)
    response1 = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response1["success"] is True

    # Cancel the friend request
    cancel_friend_request_request = cancel_friend_request.CancelFriendRequest(
        friend_id=other_user.id
    )
    response2 = await cancel_friend_request.cancel_friend_request(
        cancel_friend_request_request, auth, test_db
    )

    assert response2["success"] is True


@pytest.mark.asyncio
async def test_cancel_friend_request_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test cancel friend request with non-existent request via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    cancel_friend_request_request = cancel_friend_request.CancelFriendRequest(
        friend_id=999999
    )

    with pytest.raises(HTTPException) as exc_info:
        await cancel_friend_request.cancel_friend_request(
            cancel_friend_request_request, auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Friend request not found"


@pytest.mark.asyncio
async def test_cancel_friend_request_not_sent_by_you_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test cancel friend request with request not sent by you via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None
    other_user = await add_user("testuser3", 1003, test_db)
    assert other_user.id is not None
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    other_auth: Tuple[User, UserToken] = (other_user, other_user_token)

    # Add friend request from other user
    add_friend_request = add_friend.AddFriendRequest(user_id=test_user.id)
    response1 = await add_friend.add_friend(add_friend_request, other_auth, test_db)

    assert response1["success"] is True

    # Try to cancel the friend request from your perspective (should fail)
    cancel_friend_request_request = cancel_friend_request.CancelFriendRequest(
        friend_id=other_user.id
    )

    with pytest.raises(HTTPException) as exc_info:
        await cancel_friend_request.cancel_friend_request(
            cancel_friend_request_request, auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "You can only cancel requests you have sent"


@pytest.mark.asyncio
async def test_cancel_friend_request_already_accepted_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test cancel friend request with already accepted request via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None
    other_user = await add_user("testuser42", 1004, test_db)
    assert other_user.id is not None
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    other_auth: Tuple[User, UserToken] = (other_user, other_user_token)

    # Add friend request
    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)
    response1 = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response1["success"] is True

    # Accept the friend request
    respond_friend_request_request = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    response2 = await respond_friend_request.respond_friend_request(
        respond_friend_request_request, other_auth, test_db
    )

    assert response2["success"] is True

    # Try to cancel the friend request (should fail)
    cancel_friend_request_request = cancel_friend_request.CancelFriendRequest(
        friend_id=other_user.id
    )

    with pytest.raises(HTTPException) as exc_info:
        await cancel_friend_request.cancel_friend_request(
            cancel_friend_request_request, auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "You can only cancel requests you have sent"


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

    cancel_friend_request_request = cancel_friend_request.CancelFriendRequest(
        friend_id=1
    )
    with pytest.raises(HTTPException) as exc_info:
        await cancel_friend_request.cancel_friend_request(
            cancel_friend_request_request, auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Can't find user"
