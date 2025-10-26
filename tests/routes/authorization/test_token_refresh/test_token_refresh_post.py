"""Test for token refresh endpoint via direct post call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from tests.conftest import add_token  # pylint: disable=C0413


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
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["result"] is True
    assert "access_token" in response_json
    assert "refresh_token" in response_json


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


if __name__ == "__main__":
    pytest.main([__file__])
