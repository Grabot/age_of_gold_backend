"""Test for logout endpoint via direct post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import add_token
from src.config.config import settings


@pytest.mark.asyncio
async def test_successful_logout_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful logout with valid token."""
    _, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.post(f"{settings.API_V1_STR}/logout", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["success"]


@pytest.mark.asyncio
async def test_logout_with_invalid_token_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test logout with invalid token."""
    await add_token(1000, 1000, test_db)
    headers = {"Authorization": "Bearer invalid_token"}
    response = test_setup.post(f"{settings.API_V1_STR}/logout", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response_json = response.json()
    assert response_json["detail"] == "Authorization token is invalid or expired"


@pytest.mark.asyncio
async def test_logout_with_empty_token_post(
    test_setup: TestClient,
) -> None:
    """Test logout with empty token."""
    headers = {"Authorization": "Bearer  "}
    response = test_setup.post(f"{settings.API_V1_STR}/logout", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["detail"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
async def test_logout_with_missing_token_post(
    test_setup: TestClient,
) -> None:
    """Test logout with missing token."""
    response = test_setup.post(f"{settings.API_V1_STR}/logout")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    response_json = response.json()
    assert response_json["detail"] == "Not authenticated"
