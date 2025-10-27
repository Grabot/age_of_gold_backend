"""Test for token refresh endpoint via direct post call."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import add_token
from tests.helpers import assert_successful_response_token_key


@pytest.mark.asyncio
async def test_successful_refresh_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful token refresh via POST request."""
    _, user_token = await add_token(-1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.post(
        "/api/v1.0/login/token/refresh",
        json={"refresh_token": user_token.refresh_token},
        headers=headers,
    )
    assert_successful_response_token_key(response)


@pytest.mark.asyncio
async def test_invalid_request_invalid_tokens_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test invalid token refresh request with invalid tokens via POST request."""
    await add_token(-1000, 1000, test_db)
    headers = {"Authorization": "Bearer invalid_access_token"}
    response = test_setup.post(
        "/api/v1.0/login/token/refresh",
        json={"refresh_token": "invalid_refresh_token"},
        headers=headers,
    )
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Invalid or expired tokens"


@pytest.mark.asyncio
async def test_invalid_or_expired_tokens_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test token refresh request with invalid or expired tokens via POST request."""
    _, user_token = await add_token(-1000, -1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.post(
        "/api/v1.0/login/token/refresh",
        json={"refresh_token": user_token.refresh_token},
        headers=headers,
    )
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Invalid or expired tokens"
