"""Test for login endpoint via direct post call."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import add_token
from tests.helpers import assert_successful_response_token_key


@pytest.mark.asyncio
async def test_successful_token_login_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful login with valid token."""
    _, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.post("/api/v1.0/login/token", headers=headers)
    assert_successful_response_token_key(response)


@pytest.mark.asyncio
async def test_invalid_request_empty_bearer_post(
    test_setup: TestClient,
) -> None:
    """Test login with missing or invalid token."""
    headers = {"Authorization": "Bearer"}
    response = test_setup.post("/api/v1.0/login/token", headers=headers)
    assert response.status_code == 403
    response_json = response.json()
    assert response_json["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_invalid_token_post(
    test_setup: TestClient,
) -> None:
    """Test login with invalid token."""
    headers = {"Authorization": "Bearer invalid_access_token"}
    response = test_setup.post("/api/v1.0/login/token", headers=headers)
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["detail"] == "Authorization token is invalid or expired"
