"""Test for get multiple users endpoint via direct function call."""

from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.user import get_multiple_users
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_get_multiple_users_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful get multiple users via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user1 = await add_user("testuser1", 1001, test_db)
    other_user2 = await add_user("testuser2", 1002, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    get_users_request = get_multiple_users.GetUsersRequest(
        user_ids=[other_user1.id, other_user2.id]
    )

    response = await get_multiple_users.get_multiple_users(
        get_users_request, auth, test_db
    )

    assert response["success"] is True
    assert len(response["data"]) == 2
    user_ids_in_response = [user_data["id"] for user_data in response["data"]]
    assert other_user1.id in user_ids_in_response
    assert other_user2.id in user_ids_in_response


@pytest.mark.asyncio
async def test_get_multiple_users_empty_list_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test get multiple users with empty list via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    get_users_request = get_multiple_users.GetUsersRequest(user_ids=[])

    response = await get_multiple_users.get_multiple_users(
        get_users_request, auth, test_db
    )

    assert response["success"] is False
    assert response["message"] == "No user IDs provided"


@pytest.mark.asyncio
async def test_get_multiple_users_too_many_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test get multiple users with too many IDs via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Create a list with more than 100 user IDs
    user_ids = list(range(1, 102))
    get_users_request = get_multiple_users.GetUsersRequest(user_ids=user_ids)

    response = await get_multiple_users.get_multiple_users(
        get_users_request, auth, test_db
    )

    assert response["success"] is False
    assert response["message"] == "Too many user IDs requested (max 100)"


@pytest.mark.asyncio
async def test_get_multiple_users_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get multiple users with non-existent users via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    get_users_request = get_multiple_users.GetUsersRequest(user_ids=[999998, 999999])

    response = await get_multiple_users.get_multiple_users(
        get_users_request, auth, test_db
    )

    assert response["success"] is False
    assert response["message"] == "No users found"
