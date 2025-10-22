"""Test for token login endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

import time
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization.token_login import login_token_user  # pylint: disable=C0413
from src.models.user import User  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest.mark.asyncio
async def test_successful_token_login_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful token login via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
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

        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        response = await login_token_user(request, Response(), db)

        assert response["result"] is True
        assert "access_token" in response
        assert "refresh_token" in response


@pytest.mark.asyncio
async def test_invalid_request_no_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid request with no token via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        request = MagicMock()
        request.headers.get.return_value = "Bearer "

        response = await login_token_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
async def test_invalid_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid token via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        request = MagicMock()
        request.headers.get.return_value = "Bearer invalid_access_token"

        response = await login_token_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid or expired token"


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_database_error_during_token_login_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test database error during token login via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
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
        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise SQLAlchemyError("Database error")

        db.commit = mock_commit

        response = await login_token_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Database error: %s"
        assert isinstance(args[1], Exception)


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_integrity_error_during_token_login_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test integrity error during token login via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
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
        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise IntegrityError(
                "Integrity error", params=None, orig=Exception("Database error")
            )

        db.commit = mock_commit

        response = await login_token_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Database constraint violation: %s"
        assert isinstance(args[1], Exception)


@pytest.mark.asyncio
@patch("src.database.get_db")
@patch("src.util.gold_logging.logger.error")
async def test_unexpected_error_during_token_login_direct(
    mock_logger_error: MagicMock,
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test unexpected error during token login via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
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
        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise Exception("Unexpected error")

        db.commit = mock_commit

        response = await login_token_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Unexpected error during registration: %s"
        assert isinstance(args[1], Exception)


if __name__ == "__main__":
    pytest.main([__file__])
