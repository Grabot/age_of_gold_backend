"""Test for login endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization.login import (  # pylint: disable=C0413
    LoginRequest,
    get_user_by_username,
    login_user,
)
from src.models.user_token import UserToken  # pylint: disable=C0413
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_successful_login_with_username_direct(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful login with username."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        login_request = LoginRequest(username="testuser", password="testpassword")

        response = await login_user(login_request, Response(), db)

        user_tokens = await db.execute(select(UserToken).where(UserToken.user_id == 1))
        assert user_tokens.scalar() is not None

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_successful_login_with_email_direct(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful login with email."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        login_request = LoginRequest(
            email="testuser@example.com", password="testpassword"
        )

        response = await login_user(login_request, Response(), db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
async def test_invalid_request_missing_password_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid request with missing password."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        login_request = LoginRequest(username="testuser", password="")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_request_missing_email_and_username_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid request with missing email and username."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        login_request = LoginRequest(password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_email_or_username_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid email or username."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        login_request = LoginRequest(
            email="nonexistent@example.com", password="testpassword"
        )

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
async def test_invalid_password_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid password."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        login_request = LoginRequest(username="testuser", password="wrongpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_database_error_during_login_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test database error during login."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise SQLAlchemyError("Database error")

        db.commit = mock_commit

        login_request = LoginRequest(username="testuser", password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Database error during login: %s"
        assert isinstance(args[1], SQLAlchemyError)


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_integrity_error_during_login_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test integrity error during login."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise IntegrityError(
                "Integrity error", params=None, orig=Exception("Database error")
            )

        db.commit = mock_commit

        login_request = LoginRequest(username="testuser", password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Database integrity error during registration: %s"
        assert isinstance(args[1], IntegrityError)


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_unexpected_error_during_login_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test unexpected error during login."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise Exception("Unexpected error")

        db.commit = mock_commit
        login_request = LoginRequest(username="testuser", password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Unexpected error during login: %s"
        assert isinstance(args[1], Exception)


@pytest.mark.asyncio
async def test_get_user_by_username_none_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test get user by username with nonexistent username."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        username = "nonexistentuser"
        user = await get_user_by_username(db, username)
        assert user is None


if __name__ == "__main__":
    pytest.main([__file__])
