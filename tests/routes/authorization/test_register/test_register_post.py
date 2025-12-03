"""Test for register endpoint via direct post call."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

from src.config.config import settings
from tests.helpers import assert_successful_login


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
        f"{settings.API_V1_STR}/register",
        json={
            "email": "new_test@test.test",
            "username": "new_testuser",
            "password": "new_testpassword",
        },
    )

    assert_successful_login(
        response, expected_access_token, expected_refresh_token, status.HTTP_201_CREATED
    )
    mock_task_generate_avatar.assert_called_once()


@pytest.mark.asyncio
async def test_register_missing_fields_post_email(
    test_setup: MagicMock,
) -> None:
    """Test registration with missing email field via POST request."""
    response_email = test_setup.post(
        f"{settings.API_V1_STR}/register",
        json={
            "email": "",
            "username": "new_test2",
            "password": "new_test2password",
        },
    )

    assert response_email.status_code == 400
    response_json_email = response_email.json()
    assert response_json_email["detail"] == "Invalid request"


@pytest.mark.asyncio
async def test_register_missing_fields_post_username(
    test_setup: MagicMock,
) -> None:
    """Test registration with missing username field via POST request."""
    response_username = test_setup.post(
        f"{settings.API_V1_STR}/register",
        json={
            "email": "new_test2_2@test.test",
            "username": "",
            "password": "new_test2_2password",
        },
    )

    assert response_username.status_code == 400
    response_json_username = response_username.json()
    assert response_json_username["detail"] == "Invalid request"


@pytest.mark.asyncio
async def test_register_missing_fields_post_password(
    test_setup: MagicMock,
) -> None:
    """Test registration with missing password field via POST request."""
    response_password = test_setup.post(
        f"{settings.API_V1_STR}/register",
        json={
            "email": "new_test2_3@test.test",
            "username": "new_test2_3",
            "password": "",
        },
    )

    assert response_password.status_code == 400
    response_json_password = response_password.json()
    assert response_json_password["detail"] == "Invalid request"


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
        f"{settings.API_V1_STR}/register",
        json={
            "email": "new_test3_1@test.test",
            "username": "test_user_taken",
            "password": "new_test3_1password",
        },
    )

    assert_successful_login(
        response, expected_access_token, expected_refresh_token, 201
    )

    response = test_setup.post(
        f"{settings.API_V1_STR}/register",
        json={
            "email": "new_test3_2@test.test",
            "username": "test_user_taken",
            "password": "new_test3_2password",
        },
    )

    assert response.status_code == 409
    response_json = response.json()
    assert response_json["detail"] == "Username already taken"


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
        f"{settings.API_V1_STR}/register",
        json={
            "email": "new_test@taken.test",
            "username": "new_test4_1",
            "password": "new_test4_1password",
        },
    )

    assert_successful_login(
        response, expected_access_token, expected_refresh_token, 201
    )

    response = test_setup.post(
        f"{settings.API_V1_STR}/register",
        json={
            "email": "new_test@taken.test",
            "username": "new_test4_2",
            "password": "new_test4_2password",
        },
    )

    assert response.status_code == 409
    response_json = response.json()
    assert response_json["detail"] == "Email already used"
