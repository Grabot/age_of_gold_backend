"""Test for get user detail endpoint via direct get call."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from src.config.config import settings
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_user_detail(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful get user detail with valid token."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.get(f"{settings.API_V1_STR}/user/detail", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["success"]
    assert "data" in response_json
    assert "user" in response_json["data"]
    assert response_json["data"]["user"]["id"] == test_user.id
    assert response_json["data"]["user"]["username"] == test_user.username
