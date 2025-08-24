# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response

from main import app
from app.api.api_v1.authorization.login import LoginRequest, login_user
from tests.test_login.conftest_login import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
@patch("app.celery_worker.tasks.task_generate_avatar.delay")
async def test_successful_register_post(
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    with TestClient(app) as client:
        expected_access_token = "access_token_test"
        expected_refresh_token = "refresh_token_test"
        mock_generate_auth_token.return_value = expected_access_token
        mock_generate_refresh_token.return_value = expected_refresh_token

        response = client.post(
            "/api/v1.0/register",
            json={
                "email": "new_test@test.test",
                "username": "new_testuser",
                "password": "new_testpassword",
            },
        )
        assert response.status_code == 201
        response_json = response.json()
        assert response_json["result"] is True
        assert response_json["access_token"] == expected_access_token
        assert response_json["refresh_token"] == expected_refresh_token
        mock_task_generate_avatar.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
