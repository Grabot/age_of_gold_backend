"""Test for token refresh endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization.token_refresh import (  # pylint: disable=C0413
    RefreshRequest,
    refresh_user,
)
from tests.conftest import add_token  # pylint: disable=C0413
from tests.helpers import (  # pylint: disable=C0413
    assert_exception_error_response,
    assert_integrity_error_response,
    assert_sqalchemy_error_response,
)


@pytest.mark.asyncio
async def test_successful_refresh_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful token refresh."""
    user, user_token = await add_token(-1000, 1000, test_db)
    refresh_request = RefreshRequest(refresh_token=user_token.refresh_token)

    response = await refresh_user(
        refresh_request, Response(), user_token.access_token, test_db
    )

    assert response["result"] is True
    assert "access_token" in response
    assert "refresh_token" in response
    assert response["user"] == user.serialize


@pytest.mark.asyncio
async def test_invalid_request_no_tokens_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test invalid request with no tokens."""
    refresh_request = RefreshRequest(refresh_token="")

    response = await refresh_user(refresh_request, Response(), "", test_db)

    assert response["result"] is False
    assert response["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_request_invalid_tokens_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test invalid request with invalid tokens."""
    await add_token(-1000, 1000, test_db)
    refresh_request = RefreshRequest(refresh_token="invalid_refresh_token2")

    response = await refresh_user(
        refresh_request, Response(), "invalid_access_token2", test_db
    )

    assert response["result"] is False
    assert response["message"] == "Invalid or expired tokens"


@pytest.mark.asyncio
async def test_invalid_or_expired_tokens_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test invalid or expired tokens."""
    _, user_token = await add_token(-1000, -1000, test_db)
    refresh_request = RefreshRequest(refresh_token=user_token.refresh_token)

    response = await refresh_user(
        refresh_request, Response(), user_token.access_token, test_db
    )

    assert response["result"] is False
    assert response["message"] == "Invalid or expired tokens"


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_database_error_during_refresh_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test database error during token refresh."""
    _, user_token = await add_token(-1000, -1000, test_db)
    refresh_request = RefreshRequest(refresh_token=user_token.refresh_token)

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise SQLAlchemyError("Database error")

    mock_commit.side_effect = mock_commit_side_effect

    response = await refresh_user(
        refresh_request, Response(), user_token.access_token, test_db
    )

    assert_sqalchemy_error_response(
        response,
        mock_logger_error,
        "Token refresh failed",
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
    _, user_token = await add_token(-1000, -1000, test_db)
    refresh_request = RefreshRequest(refresh_token=user_token.refresh_token)

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError(
            "Integrity error", params=None, orig=Exception("Database error")
        )

    mock_commit.side_effect = mock_commit_side_effect

    response = await refresh_user(
        refresh_request, Response(), user_token.access_token, test_db
    )

    assert_integrity_error_response(
        response,
        mock_logger_error,
    )


@pytest.mark.asyncio
@patch("src.database.get_db")
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_unexpected_error_during_refresh_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    mock_get_db: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test unexpected error during token refresh."""
    _, user_token = await add_token(-1000, -1000, test_db)
    refresh_request = RefreshRequest(refresh_token=user_token.refresh_token)

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise Exception("Unexpected error")

    mock_commit.side_effect = mock_commit_side_effect

    response = await refresh_user(
        refresh_request, Response(), user_token.access_token, test_db
    )

    assert_exception_error_response(
        response,
        mock_logger_error,
        "Token refresh failed",
    )


if __name__ == "__main__":
    pytest.main([__file__])
