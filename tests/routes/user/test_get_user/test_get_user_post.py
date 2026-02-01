"""Test for get user endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_user_self(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful get user self with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert response.json()["data"]["id"] == user.id
    assert response.json()["data"]["username"] == user.username


@pytest.mark.asyncio
async def test_successful_get_user_other(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful get other user with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user, _ = await add_token(1001, 1001, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert response.json()["data"]["id"] == other_user.id
    assert response.json()["data"]["username"] == other_user.username


@pytest.mark.asyncio
async def test_get_user_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get user with non-existent user."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user",
        headers=headers,
        json={
            "user_id": 999999,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is False
