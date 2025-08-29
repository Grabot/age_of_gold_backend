# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.conftest import AsyncTestingSessionLocal, test_setup


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


@pytest.mark.asyncio
async def test_register_missing_fields_post(test_setup: MagicMock) -> None:
    with TestClient(app) as client:
        response_email = client.post(
            "/api/v1.0/register",
            json={
                "email": "",
                "username": "new_test2",
                "password": "new_test2password",
            },
        )

        assert response_email.status_code == 400
        response_json_email = response_email.json()
        assert response_json_email["result"] is False
        assert response_json_email["message"] == "Invalid request"

        response_username = client.post(
            "/api/v1.0/register",
            json={
                "email": "new_test3@test.test",
                "username": "",
                "password": "new_test3password",
            },
        )

        assert response_username.status_code == 400
        response_json_username = response_username.json()
        assert response_json_username["result"] is False
        assert response_json_username["message"] == "Invalid request"

        response_password = client.post(
            "/api/v1.0/register",
            json={
                "email": "new_test4@test.test",
                "username": "new_test4",
                "password": "",
            },
        )

        assert response_password.status_code == 400
        response_json_password = response_password.json()
        assert response_json_password["result"] is False
        assert response_json_password["message"] == "Invalid request"


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
@patch("app.celery_worker.tasks.task_generate_avatar.delay")
async def test_register_username_already_taken_post(
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
                "email": "new_test5@test.test",
                "username": "new_test5",
                "password": "new_test5password",
            },
        )

        assert response.status_code == 201
        response_json = response.json()
        assert response_json["result"] is True
        assert response_json["access_token"] == expected_access_token
        assert response_json["refresh_token"] == expected_refresh_token

        response = client.post(
            "/api/v1.0/register",
            json={
                "email": "new_test5_2@test.test",
                "username": "new_test5",
                "password": "new_test5password",
            },
        )

        assert response.status_code == 409
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Username already taken"


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
@patch("app.celery_worker.tasks.task_generate_avatar.delay")
async def test_register_email_already_used_post(
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
                "email": "new_test6@test.test",
                "username": "new_test6",
                "password": "new_test6password",
            },
        )

        assert response.status_code == 201
        response_json = response.json()
        assert response_json["result"] is True
        assert response_json["access_token"] == expected_access_token
        assert response_json["refresh_token"] == expected_refresh_token

        response = client.post(
            "/api/v1.0/register",
            json={
                "email": "new_test6@test.test",
                "username": "new_test6_2",
                "password": "new_test6password",
            },
        )

        assert response.status_code == 409
        response_json = response.json()
        assert response_json["result"] is False
        assert response_json["message"] == "Email already used"


if __name__ == "__main__":
    pytest.main([__file__])
