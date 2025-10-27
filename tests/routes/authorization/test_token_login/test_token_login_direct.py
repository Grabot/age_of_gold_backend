"""Test for token login endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
import time
from pathlib import Path
from typing import Any, Generator, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization import token_login  # pylint: disable=C0413
from src.models.user import User  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413
from tests.conftest import add_token  # pylint: disable=C0413
from tests.helpers import (  # pylint: disable=C0413
    assert_exception_error_response,
    assert_integrity_error_response,
    assert_sqalchemy_error_response,
)


@pytest.mark.asyncio
async def test_successful_token_login_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful token login via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (user, test_user_token)
    response = await token_login.login_token_user(Response(), auth, test_db)

    assert response["result"] is True
    assert "access_token" in response
    assert "refresh_token" in response


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_database_error_during_token_login_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test database error during token login via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise SQLAlchemyError("Database error")

    mock_commit.side_effect = mock_commit_side_effect

    auth: Tuple[User, UserToken] = (user, test_user_token)
    response = await token_login.login_token_user(Response(), auth, test_db)

    assert_sqalchemy_error_response(
        response,
        mock_logger_error,
        "Token login failed",
    )


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.delete")
async def test_integrity_error_during_token_login_direct(
    mock_delete: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test integrity error during token login via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    async def mock_delete_side_effect(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError(
            "Integrity error", params=None, orig=Exception("Database error")
        )

    mock_delete.side_effect = mock_delete_side_effect

    auth: Tuple[User, UserToken] = (user, test_user_token)
    response = await token_login.login_token_user(Response(), auth, test_db)

    assert_integrity_error_response(
        response,
        mock_logger_error,
    )


@pytest.mark.asyncio
@patch("src.database.get_db")
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.delete")
async def test_unexpected_error_during_token_login_direct(
    mock_delete: MagicMock,
    mock_logger_error: MagicMock,
    mock_get_db: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test unexpected error during token login via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    async def mock_delete_side_effect(*args: Any, **kwargs: Any) -> None:
        raise Exception("Unexpected error")

    mock_delete.side_effect = mock_delete_side_effect

    auth: Tuple[User, UserToken] = (user, test_user_token)
    response = await token_login.login_token_user(Response(), auth, test_db)

    assert_exception_error_response(
        response,
        mock_logger_error,
        "Token login failed",
    )


if __name__ == "__main__":
    pytest.main([__file__])
