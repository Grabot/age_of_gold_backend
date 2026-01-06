"""Test for respond friend request endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import respond_friend_request, add_friend
from src.models.user import User
from src.models.friend import Friend
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_accept_friend_request_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful accept friend request via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
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

    # Mock the socket emit
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response2 = await respond_friend_request.respond_friend_request(
            respond_friend_request_request, other_auth, test_db
        )

    assert response2["success"] is True

    # Assert the socket emit was called
    mock_emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_successful_reject_friend_request_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful reject friend request via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser3", 1003, test_db)
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    other_auth: Tuple[User, UserToken] = (other_user, other_user_token)

    # Add friend request
    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)
    response1 = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response1["success"] is True

    # Reject the friend request
    respond_friend_request_request = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=False
    )

    # Mock the socket emit
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response2 = await respond_friend_request.respond_friend_request(
            respond_friend_request_request, other_auth, test_db
        )

    assert response2["success"] is True

    # Assert the socket emit was called
    mock_emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_respond_friend_request_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test respond friend request with non-existent request via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    respond_friend_request_request = respond_friend_request.RespondFriendRequest(
        friend_id=999999, accept=True
    )

    with pytest.raises(HTTPException) as exc_info:
        await respond_friend_request.respond_friend_request(
            respond_friend_request_request, auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Friend request not found"


@pytest.mark.asyncio
async def test_respond_friend_request_already_accepted_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test respond friend request with already accepted request via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser14", 1004, test_db)
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

    # Try to accept again (should fail)
    with pytest.raises(HTTPException) as exc_info:
        await respond_friend_request.respond_friend_request(
            respond_friend_request_request, other_auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Friend request already accepted"


@pytest.mark.asyncio
async def test_respond_friend_request_you_sent_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test respond friend request with request you sent via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser55", 10055, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Add friend request
    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)
    response1 = await add_friend.add_friend(add_friend_request, auth, test_db)

    assert response1["success"] is True

    # Try to respond to your own request (should fail)
    respond_friend_request_request = respond_friend_request.RespondFriendRequest(
        friend_id=other_user.id, accept=True
    )

    with pytest.raises(HTTPException) as exc_info:
        await respond_friend_request.respond_friend_request(
            respond_friend_request_request, auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "You cannot respond to a request you sent"

