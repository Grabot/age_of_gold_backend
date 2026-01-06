"""Test for get avatar version endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_avatar_version(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful get avatar version with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user, _ = await add_token(1001, 1001, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/avatar/version",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert response.json()["data"] == other_user.avatar_version


@pytest.mark.asyncio
async def test_get_avatar_version_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get avatar version with non-existent user."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/avatar/version",
        headers=headers,
        json={
            "user_id": 999999,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is False
