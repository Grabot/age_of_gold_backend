"""Test for logout endpoint via direct post call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

import time
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import pytest_asyncio

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.database import get_db  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413
from main import app  # pylint: disable=C0413
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest_asyncio.fixture
async def db_with_token(test_setup: TestClient) -> AsyncGenerator[AsyncSession, None]:
    """Fixture that creates a token and overrides get_db with the current session."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        test_user_token = UserToken(
            user_id=1,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

        async def get_db_override():
            yield db

        app.dependency_overrides[get_db] = get_db_override
        yield db
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_successful_logout_post(
    test_setup: TestClient,
    db_with_token: AsyncSession,
) -> None:
    """Test successful logout with valid token."""
    headers = {"Authorization": "Bearer test_access_token"}
    response = test_setup.post("/api/v1.0/logout", headers=headers)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["result"] is True
    assert response_json["message"] == "User logged out successfully."


@pytest.mark.asyncio
async def test_logout_with_invalid_token_post(
    test_setup: TestClient,
    db_with_token: AsyncSession,
) -> None:
    """Test logout with invalid token."""
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


if __name__ == "__main__":
    pytest.main([__file__])
