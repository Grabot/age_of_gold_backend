"""Test for login endpoint via direct post call."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from src.config.config import settings
from tests.helpers import assert_successful_login


@pytest.mark.asyncio
async def test_successful_login_with_username_post(
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: TestClient,
) -> None:
    """Test successful login with username using POST request."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens

    response = test_setup.post(
        f"{settings.API_V1_STR}/login",
        json={"username": "testuser", "password": "testpassword"},
    )
    assert_successful_login(response, expected_access_token, expected_refresh_token)


@pytest.mark.asyncio
async def test_successful_login_with_email_post(
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: TestClient,
) -> None:
    """Test successful login with email using POST request."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens

    response = test_setup.post(
        f"{settings.API_V1_STR}/login",
        json={"email": "testuser@example.com", "password": "testpassword"},
    )

    assert_successful_login(response, expected_access_token, expected_refresh_token)


@pytest.mark.asyncio
async def test_invalid_request_missing_password_post(
    test_setup: TestClient,
) -> None:
    """Test invalid request with missing password using POST request."""
    response = test_setup.post(
        f"{settings.API_V1_STR}/login", json={"username": "testuser", "password": ""}
    )
    assert response.status_code == 400
    response_json = response.json()
    assert response_json["detail"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_request_missing_email_and_username_post(
    test_setup: TestClient,
) -> None:
    """Test invalid request with missing email and username using POST request."""
    response = test_setup.post(
        f"{settings.API_V1_STR}/login", json={"password": "testpassword"}
    )
    assert response.status_code == 400
    response_json = response.json()
    assert response_json["detail"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_email_or_username_post(
    test_setup: TestClient,
) -> None:
    """Test invalid email or username using POST request."""
    response = test_setup.post(
        f"{settings.API_V1_STR}/login",
        json={"email": "nonexistent@example.com", "password": "testpassword"},
    )
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["detail"] == "Invalid email/username or password"


@pytest.mark.asyncio
async def test_invalid_password_post(
    test_setup: TestClient,
) -> None:
    """Test invalid password using POST request."""
    response = test_setup.post(
        f"{settings.API_V1_STR}/login",
        json={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["detail"] == "Invalid email/username or password"


@pytest.mark.asyncio
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_database_error_during_login_post(
    mock_commit: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test database error during login using POST request."""

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise SQLAlchemyError("Database error")

    mock_commit.side_effect = mock_commit_side_effect
    response = test_setup.post(
        f"{settings.API_V1_STR}/login",
        json={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 500
    response_json = response.json()
    assert response_json["detail"] == "Login failed"


@pytest.mark.asyncio
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_unexpected_error_during_login_post(
    mock_commit: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test unexpected error during login using POST request."""

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise Exception("Unexpected error")

    mock_commit.side_effect = mock_commit_side_effect
    response = test_setup.post(
        f"{settings.API_V1_STR}/login",
        json={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 500
    response_json = response.json()
    assert response_json["detail"] == "Login failed"
