"""Test for search friend endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_search_friend(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful search friend with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/search",
        headers=headers,
        json={
            "username": other_user.username,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert response.json()["data"]["username"] == other_user.username


@pytest.mark.asyncio
async def test_search_friend_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test search friend with non-existent user."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/search",
        headers=headers,
        json={
            "username": "nonexistentuser",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_search_friend_case_insensitive(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test search friend with case insensitive username."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser3", 1003, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/search",
        headers=headers,
        json={
            "username": other_user.username.upper(),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert response.json()["data"]["username"] == other_user.username
