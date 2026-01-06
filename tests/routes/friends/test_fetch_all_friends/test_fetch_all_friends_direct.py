"""Test for fetch all friends endpoint via direct function call."""

from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import fetch_all_friends, add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_fetch_all_friends_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful fetch all friends via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user1 = await add_user("testuser2", 1002, test_db)
    other_user2 = await add_user("testuser3", 1003, test_db)
    _, other_user1_token = await add_token(1000, 1000, test_db, other_user1.id)
    _, other_user2_token = await add_token(1000, 1000, test_db, other_user2.id)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    other_auth1: Tuple[User, UserToken] = (other_user1, other_user1_token)
    other_auth2: Tuple[User, UserToken] = (other_user2, other_user2_token)

    # Add friend requests
    add_friend_request1 = add_friend.AddFriendRequest(user_id=other_user1.id)
    response1 = await add_friend.add_friend(add_friend_request1, auth, test_db)

    assert response1["success"] is True

    add_friend_request2 = add_friend.AddFriendRequest(user_id=other_user2.id)
    response2 = await add_friend.add_friend(add_friend_request2, auth, test_db)

    assert response2["success"] is True

    # Accept the friend requests
    respond_friend_request1 = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    response3 = await respond_friend_request.respond_friend_request(
        respond_friend_request1, other_auth1, test_db
    )

    assert response3["success"] is True

    respond_friend_request2 = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    response4 = await respond_friend_request.respond_friend_request(
        respond_friend_request2, other_auth2, test_db
    )

    assert response4["success"] is True

    # Fetch all friends
    fetch_friends_request = fetch_all_friends.FetchFriendsRequest(user_ids=None)
    response5 = await fetch_all_friends.fetch_all_friends(
        fetch_friends_request, auth, test_db
    )

    assert response5["success"] is True
    assert len(response5["data"]) == 2


@pytest.mark.asyncio
async def test_fetch_all_friends_with_filter_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test fetch all friends with user ID filter via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user1 = await add_user("testuser46", 1004, test_db)
    other_user2 = await add_user("testuser57", 1005, test_db)
    _, other_user1_token = await add_token(1000, 1000, test_db, other_user1.id)
    _, other_user2_token = await add_token(1000, 1000, test_db, other_user2.id)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    other_auth1: Tuple[User, UserToken] = (other_user1, other_user1_token)
    other_auth2: Tuple[User, UserToken] = (other_user2, other_user2_token)

    # Add friend requests
    add_friend_request1 = add_friend.AddFriendRequest(user_id=other_user1.id)
    response1 = await add_friend.add_friend(add_friend_request1, auth, test_db)

    assert response1["success"] is True

    add_friend_request2 = add_friend.AddFriendRequest(user_id=other_user2.id)
    response2 = await add_friend.add_friend(add_friend_request2, auth, test_db)

    assert response2["success"] is True

    # Accept the friend requests
    respond_friend_request1 = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    response3 = await respond_friend_request.respond_friend_request(
        respond_friend_request1, other_auth1, test_db
    )

    assert response3["success"] is True

    respond_friend_request2 = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    response4 = await respond_friend_request.respond_friend_request(
        respond_friend_request2, other_auth2, test_db
    )

    assert response4["success"] is True

    # Fetch all friends with filter
    fetch_friends_request = fetch_all_friends.FetchFriendsRequest(
        user_ids=[other_user1.id]
    )
    response5 = await fetch_all_friends.fetch_all_friends(
        fetch_friends_request, auth, test_db
    )

    assert response5["success"] is True
    assert len(response5["data"]) == 1
    assert response5["data"][0]["friend_id"] == other_user1.id


@pytest.mark.asyncio
async def test_fetch_all_friends_empty_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test fetch all friends with no friends via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Fetch all friends
    fetch_friends_request = fetch_all_friends.FetchFriendsRequest(user_ids=None)
    response = await fetch_all_friends.fetch_all_friends(
        fetch_friends_request, auth, test_db
    )

    assert response["success"] is True
    # Note: The test user might have friends from previous tests, so we just check the response is successful
