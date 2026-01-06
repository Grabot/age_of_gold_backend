"""Test for search friend endpoint via direct function call."""

from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import search_friend
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_search_friend_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful search friend via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    search_friend_request = search_friend.SearchFriendRequest(
        username=other_user.username
    )

    response = await search_friend.search_friend(search_friend_request, auth, test_db)

    assert response["success"] is True
    assert response["data"]["username"] == other_user.username


@pytest.mark.asyncio
async def test_search_friend_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test search friend with non-existent user via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    search_friend_request = search_friend.SearchFriendRequest(
        username="nonexistentuser"
    )

    response = await search_friend.search_friend(search_friend_request, auth, test_db)

    assert response["success"] is False


@pytest.mark.asyncio
async def test_search_friend_case_insensitive_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test search friend with case insensitive username via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser3", 1003, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    search_friend_request = search_friend.SearchFriendRequest(
        username=other_user.username.upper()
    )

    response = await search_friend.search_friend(search_friend_request, auth, test_db)

    assert response["success"] is True
    assert response["data"]["username"] == other_user.username
