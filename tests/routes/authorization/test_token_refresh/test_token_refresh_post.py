"""Test for token refresh endpoint via direct post call."""

# ruff: noqa: E402, F401, F811
import sys
import time
from pathlib import Path

from typing import Any, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from tests.conftest import add_token  # pylint: disable=C0413
from src.models.user import User  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413
from main import app  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("src.database.get_db")
async def test_successful_refresh_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful token refresh via POST request."""
    user = await add_token(-1000, 1000)

    with TestClient(app) as client:
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.post(
            "/api/v1.0/login/token/refresh",
            json={"refresh_token": "valid_refresh_token"},
            headers=headers,
        )
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["result"] is True
        assert "access_token" in response_json
        assert "refresh_token" in response_json
        assert response_json["user"] == user.serialize


@pytest.mark.asyncio
@patch("src.database.get_db")
async def test_invalid_request_no_tokens_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid token refresh request with no tokens via POST request."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1.0/login/token/refresh",
            json={"refresh_token": ""},
        )
        assert response.status_code == 401
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
@patch("src.database.get_db")
async def test_invalid_request_invalid_tokens_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid token refresh request with invalid tokens via POST request."""
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer invalid_access_token"}
        response = client.post(
            "/api/v1.0/login/token/refresh",
            json={"refresh_token": "invalid_refresh_token"},
            headers=headers,
        )
        assert response.status_code == 401
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Invalid or expired tokens"


@pytest.mark.asyncio
@patch("src.database.get_db")
async def test_invalid_or_expired_tokens_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test token refresh request with invalid or expired tokens via POST request."""
    await add_token(-1000, -1000)
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.post(
            "/api/v1.0/login/token/refresh",
            json={"refresh_token": "valid_refresh_token"},
            headers=headers,
        )
        assert response.status_code == 401
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Invalid or expired tokens"


if __name__ == "__main__":
    pytest.main([__file__])
