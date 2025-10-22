"""Test for login endpoint via direct post call."""

# ruff: noqa: E402, F401, F811
import sys
import time
from pathlib import Path

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.models.user import User  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413
from main import app  # pylint: disable=C0413
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("src.database.get_db")
async def test_successful_token_login_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful login with valid token."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user = await db.get(User, 1)
        user_token = UserToken(
            user_id=user.id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(user_token)
        await db.commit()

    with TestClient(app) as client:
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.post("/api/v1.0/login/token", headers=headers)
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["result"] is True
        assert "access_token" in response_json
        assert "refresh_token" in response_json


@pytest.mark.asyncio
@patch("src.database.get_db")
async def test_invalid_request_no_token_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test login with missing or invalid token."""
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer "}
        response = client.post("/api/v1.0/login/token", headers=headers)
        assert response.status_code == 400
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
@patch("src.database.get_db")
async def test_invalid_token_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test login with invalid token."""
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer invalid_access_token"}
        response = client.post("/api/v1.0/login/token", headers=headers)
        assert response.status_code == 401
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Invalid or expired token"


if __name__ == "__main__":
    pytest.main([__file__])
