"""Test for register endpoint via direct post call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from tests.helpers import assert_successful_response_token  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
async def test_successful_register_post(
    mock_task_generate_avatar: MagicMock,
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: MagicMock,
) -> None:
    """Test successful registration via POST request."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens

    response = test_setup.post(
        "/api/v1.0/register",
        json={
            "email": "new_test@test.test",
            "username": "new_testuser",
            "password": "new_testpassword",
        },
    )
    # DOING
    assert_successful_response_token(
        response, expected_access_token, expected_refresh_token, 201
    )
    mock_task_generate_avatar.assert_called_once()


@pytest.mark.asyncio
async def test_register_missing_fields_post(
    test_setup: MagicMock,
) -> None:
    """Test registration with missing fields via POST request."""
    response_email = test_setup.post(
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

    response_username = test_setup.post(
        "/api/v1.0/register",
        json={
            "email": "new_test2_2@test.test",
            "username": "",
            "password": "new_test2_2password",
        },
    )

    assert response_username.status_code == 400
    response_json_username = response_username.json()
    assert response_json_username["result"] is False
    assert response_json_username["message"] == "Invalid request"

    response_password = test_setup.post(
        "/api/v1.0/register",
        json={
            "email": "new_test2_3@test.test",
            "username": "new_test2_3",
            "password": "",
        },
    )

    assert response_password.status_code == 400
    response_json_password = response_password.json()
    assert response_json_password["result"] is False
    assert response_json_password["message"] == "Invalid request"


@pytest.mark.asyncio
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
async def test_register_username_already_taken_post(
    mock_task_generate_avatar: MagicMock,
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: MagicMock,
) -> None:
    """Test registration with an already taken username via POST request."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens

    response = test_setup.post(
        "/api/v1.0/register",
        json={
            "email": "new_test3_1@test.test",
            "username": "test_user_taken",
            "password": "new_test3_1password",
        },
    )

    assert_successful_response_token(
        response, expected_access_token, expected_refresh_token, 201
    )

    response = test_setup.post(
        "/api/v1.0/register",
        json={
            "email": "new_test3_2@test.test",
            "username": "test_user_taken",
            "password": "new_test3_2password",
        },
    )

    assert response.status_code == 409
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Username already taken"


@pytest.mark.asyncio
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
async def test_register_email_already_used_post(
    mock_task_generate_avatar: MagicMock,
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: MagicMock,
) -> None:
    """Test registration with an already used email via POST request."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens

    response = test_setup.post(
        "/api/v1.0/register",
        json={
            "email": "new_test@taken.test",
            "username": "new_test4_1",
            "password": "new_test4_1password",
        },
    )

    assert_successful_response_token(
        response, expected_access_token, expected_refresh_token, 201
    )

    response = test_setup.post(
        "/api/v1.0/register",
        json={
            "email": "new_test@taken.test",
            "username": "new_test4_2",
            "password": "new_test4_2password",
        },
    )

    assert response.status_code == 409
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Email already used"


if __name__ == "__main__":
    pytest.main([__file__])
