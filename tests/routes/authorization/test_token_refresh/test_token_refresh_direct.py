"""Test for token refresh endpoint via direct function call."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.authorization import token_refresh
from src.util.util import SuccessfulLoginResponse
from tests.conftest import add_token
from tests.helpers import (
    assert_exception_error_response,
    assert_integrity_error_response,
    assert_sqalchemy_error_response,
    assert_successful_login_dict_key,
)


@pytest.mark.asyncio
async def test_successful_refresh_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful token refresh."""
    _, user_token = await add_token(-1000, 1000, test_db)
    refresh_request = token_refresh.RefreshRequest(
        refresh_token=user_token.refresh_token
    )

    response_dict: SuccessfulLoginResponse = await token_refresh.refresh_user(
        refresh_request, user_token.access_token, test_db
    )

    assert_successful_login_dict_key(response_dict)


@pytest.mark.asyncio
async def test_invalid_request_no_tokens_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test invalid request with no tokens."""
    refresh_request = token_refresh.RefreshRequest(refresh_token="")

    with pytest.raises(HTTPException) as exc_info:
        await token_refresh.refresh_user(refresh_request, "", test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_request_invalid_tokens_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test invalid request with invalid tokens."""
    await add_token(-1000, 1000, test_db)
    refresh_request = token_refresh.RefreshRequest(
        refresh_token="invalid_refresh_token2"
    )
    with pytest.raises(HTTPException) as exc_info:
        await token_refresh.refresh_user(
            refresh_request, "invalid_access_token2", test_db
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Invalid or expired tokens"


@pytest.mark.asyncio
async def test_invalid_or_expired_tokens_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test invalid or expired tokens."""
    _, user_token = await add_token(-1000, -1000, test_db)
    refresh_request = token_refresh.RefreshRequest(
        refresh_token=user_token.refresh_token
    )
    with pytest.raises(HTTPException) as exc_info:
        await token_refresh.refresh_user(
            refresh_request, user_token.access_token, test_db
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Invalid or expired tokens"


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
    refresh_request = token_refresh.RefreshRequest(
        refresh_token=user_token.refresh_token
    )

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise SQLAlchemyError("Database error")

    mock_commit.side_effect = mock_commit_side_effect
    with pytest.raises(HTTPException) as exc_info:
        await token_refresh.refresh_user(
            refresh_request, user_token.access_token, test_db
        )

    assert_sqalchemy_error_response(
        exc_info.value,
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
    refresh_request = token_refresh.RefreshRequest(
        refresh_token=user_token.refresh_token
    )

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError(
            "Integrity error", params=None, orig=Exception("Database error")
        )

    mock_commit.side_effect = mock_commit_side_effect
    with pytest.raises(HTTPException) as exc_info:
        await token_refresh.refresh_user(
            refresh_request, user_token.access_token, test_db
        )

    assert_integrity_error_response(
        exc_info.value,
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
    refresh_request = token_refresh.RefreshRequest(
        refresh_token=user_token.refresh_token
    )

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise Exception("Unexpected error")

    mock_commit.side_effect = mock_commit_side_effect
    with pytest.raises(HTTPException) as exc_info:
        await token_refresh.refresh_user(
            refresh_request, user_token.access_token, test_db
        )

    assert_exception_error_response(
        exc_info.value,
        mock_logger_error,
        "Token refresh failed",
    )
