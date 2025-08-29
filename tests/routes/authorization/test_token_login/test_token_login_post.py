# ruff: noqa: E402, F401, F811
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.user_token import UserToken
from main import app
from tests.conftest import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
@patch("app.database.get_db")
async def test_successful_token_login_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
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
        response = client.post(
            "/api/v1.0/login/token", json={"access_token": "valid_access_token"}
        )
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["result"] is True
        assert response_json["message"] == "User logged in successfully."
        assert "access_token" in response_json
        assert "refresh_token" in response_json
        assert response_json["user"] == user.serialize


@pytest.mark.asyncio
@patch("app.database.get_db")
async def test_invalid_request_no_token_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1.0/login/token", json={"access_token": ""})
        assert response.status_code == 400
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Invalid request"


@pytest.mark.asyncio
@patch("app.database.get_db")
async def test_invalid_token_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1.0/login/token", json={"access_token": "invalid_access_token"}
        )
        assert response.status_code == 401
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Invalid or expired token"


if __name__ == "__main__":
    pytest.main([__file__])
