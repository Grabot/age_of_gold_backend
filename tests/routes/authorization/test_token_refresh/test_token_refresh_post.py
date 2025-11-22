"""Test for token refresh endpoint via direct post call."""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import add_token
from tests.helpers import assert_successful_login_key
from src.config.config import settings


@pytest.mark.asyncio
async def test_successful_refresh_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful token refresh via POST request."""
    _, user_token = await add_token(-1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.post(
        f"{settings.API_V1_STR}/login/token/refresh",
        json={"refresh_token": user_token.refresh_token},
        headers=headers,
    )
    assert_successful_login_key(response)


@pytest.mark.asyncio
async def test_invalid_request_invalid_tokens_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test invalid token refresh request with invalid tokens via POST request."""
    await add_token(-1000, 1000, test_db)
    headers = {"Authorization": "Bearer invalid_access_token"}
    response = test_setup.post(
        f"{settings.API_V1_STR}/login/token/refresh",
        json={"refresh_token": "invalid_refresh_token"},
        headers=headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["detail"] == "Invalid or expired tokens"


@pytest.mark.asyncio
async def test_invalid_or_expired_tokens_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test token refresh request with invalid or expired tokens via POST request."""
    _, user_token = await add_token(-1000, -1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.post(
        f"{settings.API_V1_STR}/login/token/refresh",
        json={"refresh_token": user_token.refresh_token},
        headers=headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["detail"] == "Invalid or expired tokens"
