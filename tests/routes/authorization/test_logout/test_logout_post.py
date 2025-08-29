# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

import time
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.api_v1.authorization.logout import logout_user
from app.models.user import User
from app.models.user_token import UserToken
from main import app
from tests.conftest import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
@patch("app.database.get_db")
async def test_successful_logout_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        test_user_token = UserToken(
            user_id=user.id,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

    with TestClient(app) as client:
        headers = {"Authorization": "Bearer test_access_token"}
        response = client.post("/api/v1.0/logout", headers=headers)
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["result"] is True
        assert response_json["message"] == "User logged out successfully."


@pytest.mark.asyncio
@patch("app.database.get_db")
async def test_logout_with_invalid_token_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1.0/logout", headers=headers)
        assert response.status_code == 401
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "User not found or token expired"


@pytest.mark.asyncio
@patch("app.database.get_db")
async def test_logout_with_missing_token_post(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1.0/logout")
        assert response.status_code == 401
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Authorization token is missing or invalid"


if __name__ == "__main__":
    pytest.main([__file__])
