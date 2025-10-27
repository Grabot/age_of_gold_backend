"""Test for logout endpoint via direct post call."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import add_token
from tests.helpers import assert_successful_response


@pytest.mark.asyncio
async def test_successful_logout_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful logout with valid token."""
    _, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.post("/api/v1.0/logout", headers=headers)
    response_json = assert_successful_response(response)
    assert response_json["message"] == "User logged out successfully."


@pytest.mark.asyncio
async def test_logout_with_invalid_token_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test logout with invalid token."""
    await add_token(1000, 1000, test_db)
    headers = {"Authorization": "Bearer invalid_token"}
    response = test_setup.post("/api/v1.0/logout", headers=headers)
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["detail"] == "Authorization token is invalid or expired"


@pytest.mark.asyncio
async def test_logout_with_empty_token_post(
    test_setup: TestClient,
) -> None:
    """Test logout with empty token."""
    headers = {"Authorization": "Bearer  "}
    response = test_setup.post("/api/v1.0/logout", headers=headers)
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["detail"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
async def test_logout_with_missing_token_post(
    test_setup: TestClient,
) -> None:
    """Test logout with missing token."""
    response = test_setup.post("/api/v1.0/logout")
    assert response.status_code == 403
    response_json = response.json()
    assert response_json["detail"] == "Not authenticated"
