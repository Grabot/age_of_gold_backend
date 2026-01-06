"""Test for get multiple users endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_get_multiple_users(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful get multiple users with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user1 = await add_user("testuser1", 1001, test_db)
    other_user2 = await add_user("testuser2", 1002, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/get-multiple",
        headers=headers,
        json={
            "user_ids": [other_user1.id, other_user2.id],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert len(response.json()["data"]) == 2
    user_ids_in_response = [user_data["id"] for user_data in response.json()["data"]]
    assert other_user1.id in user_ids_in_response
    assert other_user2.id in user_ids_in_response


@pytest.mark.asyncio
async def test_get_multiple_users_empty_list(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get multiple users with empty list."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/get-multiple",
        headers=headers,
        json={
            "user_ids": [],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is False
    assert response.json()["message"] == "No user IDs provided"


@pytest.mark.asyncio
async def test_get_multiple_users_too_many(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get multiple users with too many IDs."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    # Create a list with more than 100 user IDs
    user_ids = list(range(1, 102))

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/get-multiple",
        headers=headers,
        json={
            "user_ids": user_ids,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is False
    assert response.json()["message"] == "Too many user IDs requested (max 100)"


@pytest.mark.asyncio
async def test_get_multiple_users_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get multiple users with non-existent users."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/get-multiple",
        headers=headers,
        json={
            "user_ids": [999998, 999999],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is False
    assert response.json()["message"] == "No users found"
