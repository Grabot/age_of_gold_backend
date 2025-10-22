"""Test for logout endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

import time
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization.logout import logout_user  # pylint: disable=C0413
from src.models.user import User  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest.mark.asyncio
async def test_successful_logout_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful logout via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_id = 1
        user = await db.get(User, user_id)
        assert user is not None
        test_user_token = UserToken(
            user_id=user_id,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

        request = MagicMock()
        request.headers.get.return_value = "Bearer test_access_token"

        response = await logout_user(request, Response(), db)

        user_tokens = await db.execute(select(UserToken).where(UserToken.user_id == 1))
        assert user_tokens.scalar() is None

        assert response["result"] is True
        assert response["message"] == "User logged out successfully."


@pytest.mark.asyncio
async def test_logout_with_invalid_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test logout with invalid token via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        request = MagicMock()
        request.headers.get.return_value = "Bearer invalid_token"

        response = await logout_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "User not found or token expired"


@pytest.mark.asyncio
async def test_logout_with_missing_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test logout with missing token via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        request = MagicMock()
        request.headers.get.return_value = None

        response = await logout_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_database_error_during_login_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test database error during logout via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_id = 1
        user = await db.get(User, user_id)
        assert user is not None
        test_user_token = UserToken(
            user_id=user_id,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

        async def mock_delete(*args: Any, **kwargs: Any) -> None:
            raise SQLAlchemyError("Database error")

        db.delete = mock_delete

        request = MagicMock()
        request.headers.get.return_value = "Bearer test_access_token"

        response = await logout_user(request, Response(), db)

        assert not response["result"]
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Database error during logout: %s"
        assert isinstance(args[1], Exception)


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_unexpected_error_during_logout_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test unexpected error during logout via direct function call."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_id = 1
        user = await db.get(User, user_id)
        assert user is not None
        test_user_token = UserToken(
            user_id=user_id,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

        async def mock_delete(*args: Any, **kwargs: Any) -> None:
            raise Exception("Unexpected error")

        db.delete = mock_delete

        request = MagicMock()
        request.headers.get.return_value = "Bearer test_access_token"

        response = await logout_user(request, Response(), db)

        assert not response["result"]
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Unexpected error during logout: %s"
        assert isinstance(args[1], Exception)


if __name__ == "__main__":
    pytest.main([__file__])
