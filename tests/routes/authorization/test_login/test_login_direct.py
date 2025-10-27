"""Test for login endpoint via direct function call."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.authorization import login
from src.models.user_token import UserToken
from tests.helpers import (
    assert_exception_error_response,
    assert_integrity_error_response,
    assert_sqalchemy_error_response,
)


@pytest.mark.asyncio
async def test_successful_login_with_username_direct(
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful login with username."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens
    login_request = login.LoginRequest(username="testuser", password="testpassword")

    response = await login.login_user(login_request, Response(), test_db)

    user_tokens = await test_db.execute(select(UserToken).where(UserToken.user_id == 1))
    assert user_tokens.scalar() is not None

    assert response["result"] is True
    assert response["access_token"] == expected_access_token
    assert response["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
async def test_successful_login_with_email_direct(
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful login with email."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens
    login_request = login.LoginRequest(
        email="testuser@example.com", password="testpassword"
    )

    response = await login.login_user(login_request, Response(), test_db)

    assert response["result"] is True
    assert response["access_token"] == expected_access_token
    assert response["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
async def test_invalid_request_missing_password_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test invalid request with missing password."""
    login_request = login.LoginRequest(username="testuser", password="")

    response = await login.login_user(login_request, Response(), test_db)

    assert response["result"] is False
    assert response["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_request_missing_email_and_username_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test invalid request with missing email and username."""
    login_request = login.LoginRequest(password="testpassword")

    response = await login.login_user(login_request, Response(), test_db)

    assert response["result"] is False
    assert response["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_email_or_username_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test invalid email or username."""
    login_request = login.LoginRequest(
        email="nonexistent@example.com", password="testpassword"
    )

    response = await login.login_user(login_request, Response(), test_db)

    assert response["result"] is False
    assert response["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
async def test_invalid_password_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test invalid password."""
    login_request = login.LoginRequest(username="testuser", password="wrongpassword")

    response = await login.login_user(login_request, Response(), test_db)

    assert response["result"] is False
    assert response["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_database_error_during_login_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test database error during login."""

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise SQLAlchemyError("Database error")

    mock_commit.side_effect = mock_commit_side_effect

    login_request = login.LoginRequest(username="testuser", password="testpassword")

    response = await login.login_user(login_request, Response(), test_db)

    assert_sqalchemy_error_response(
        response,
        mock_logger_error,
        "Login failed",
    )


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_integrity_error_during_login_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test integrity error during login."""

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError(
            "Integrity error", params=None, orig=Exception("Database error")
        )

    mock_commit.side_effect = mock_commit_side_effect

    login_request = login.LoginRequest(username="testuser", password="testpassword")

    response = await login.login_user(login_request, Response(), test_db)

    assert_integrity_error_response(
        response,
        mock_logger_error,
    )


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_unexpected_error_during_login_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test unexpected error during login."""

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise Exception("Unexpected error")

    mock_commit.side_effect = mock_commit_side_effect

    login_request = login.LoginRequest(username="testuser", password="testpassword")

    response = await login.login_user(login_request, Response(), test_db)

    assert_exception_error_response(response, mock_logger_error, "Login failed")


@pytest.mark.asyncio
async def test_get_user_by_username_none_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get user by username with nonexistent username."""
    username = "nonexistentuser"
    user = await login.get_user_by_username(test_db, username)
    assert user is None
