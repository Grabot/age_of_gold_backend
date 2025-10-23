"""Test for token refresh endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
import time
from pathlib import Path

from typing import Any, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from tests.conftest import ASYNC_TESTING_SESSION_LOCAL, add_token  # pylint: disable=C0413
from src.api.api_v1.authorization.token_refresh import (  # pylint: disable=C0413
    RefreshRequest,
    refresh_user,
)
from src.models.user import User  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413


@pytest.mark.asyncio
async def test_successful_refresh_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful token refresh."""
    user = await add_token(-1000, 1000)
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        refresh_request = RefreshRequest(refresh_token="valid_refresh_token")

        response = await refresh_user(request, refresh_request, Response(), db)

        assert response["result"] is True
        assert "access_token" in response
        assert "refresh_token" in response
        assert response["user"] == user.serialize


@pytest.mark.asyncio
async def test_invalid_request_no_tokens_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid request with no tokens."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        request = MagicMock()
        request.headers.get.return_value = None

        refresh_request = RefreshRequest(refresh_token="")

        response = await refresh_user(request, refresh_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
async def test_invalid_request_invalid_tokens_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid request with invalid tokens."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        request = MagicMock()
        request.headers.get.return_value = "Bearer invalid_access_token"

        refresh_request = RefreshRequest(refresh_token="invalid_refresh_token")

        response = await refresh_user(request, refresh_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid or expired tokens"


@pytest.mark.asyncio
async def test_invalid_or_expired_tokens_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test invalid or expired tokens."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_id = 1
        user: Optional[User] = await db.get(User, user_id)
        assert user is not None
        user_token = UserToken(
            user_id=user_id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) - 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) - 1000,
        )
        db.add(user_token)
        await db.commit()

        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        refresh_request = RefreshRequest(refresh_token="valid_refresh_token")

        response = await refresh_user(request, refresh_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid or expired tokens"


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_database_error_during_refresh_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test database error during token refresh."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_id = 1
        user: Optional[User] = await db.get(User, user_id)
        assert user is not None
        user_token = UserToken(
            user_id=user_id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) - 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) - 1000,
        )
        db.add(user_token)
        await db.commit()

        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        refresh_request = RefreshRequest(refresh_token="valid_refresh_token")

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise SQLAlchemyError("Database error")

        db.commit = mock_commit

        response = await refresh_user(request, refresh_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Database error during token refresh: %s"
        assert isinstance(args[1], SQLAlchemyError)


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_integrity_error_during_login_direct(
    mock_logger_error: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test integrity error during login."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_id = 1
        user: Optional[User] = await db.get(User, user_id)
        assert user is not None
        user_token = UserToken(
            user_id=user_id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) - 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) - 1000,
        )
        db.add(user_token)
        await db.commit()

        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        refresh_request = RefreshRequest(refresh_token="valid_refresh_token")

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise IntegrityError(
                "Integrity error", params=None, orig=Exception("Database error")
            )

        db.commit = mock_commit

        response = await refresh_user(request, refresh_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Database integrity error during registration: %s"
        assert isinstance(args[1], IntegrityError)


@pytest.mark.asyncio
@patch("src.database.get_db")
@patch("src.util.gold_logging.logger.error")
async def test_unexpected_error_during_refresh_direct(
    mock_logger_error: MagicMock,
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test unexpected error during token refresh."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_id = 1
        user: Optional[User] = await db.get(User, user_id)
        assert user is not None
        user_token = UserToken(
            user_id=user_id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) - 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) - 1000,
        )
        db.add(user_token)
        await db.commit()

        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_access_token"

        refresh_request = RefreshRequest(refresh_token="valid_refresh_token")

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise Exception("Unexpected error")

        db.commit = mock_commit

        response = await refresh_user(request, refresh_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"
        mock_logger_error.assert_called_once()
        args, _ = mock_logger_error.call_args
        assert args[0] == "Unexpected error during token refresh: %s"
        assert isinstance(args[1], Exception)


if __name__ == "__main__":
    pytest.main([__file__])
