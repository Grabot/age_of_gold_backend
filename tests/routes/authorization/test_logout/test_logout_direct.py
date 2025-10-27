"""Test for logout endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path
from typing import Any, Tuple
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization import logout  # pylint: disable=C0413
from src.models.user import User  # pylint: disable=C0413
from src.models.user_token import UserToken  # pylint: disable=C0413
from tests.conftest import add_token  # pylint: disable=C0413
from tests.helpers import (  # pylint: disable=C0413
    assert_exception_error_response,
    assert_sqalchemy_error_response,
)


@pytest.mark.asyncio
async def test_successful_logout_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful logout via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (user, test_user_token)
    response = await logout.logout_user(Response(), auth, test_db)

    user_tokens = await test_db.execute(select(UserToken).where(UserToken.user_id == 1))
    assert user_tokens.scalar() is None

    assert response["result"] is True
    assert response["message"] == "User logged out successfully."


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.delete")
async def test_database_error_during_login_direct(
    mock_delete: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test database error during logout via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    async def mock_delete_side_effect(*args: Any, **kwargs: Any) -> None:
        raise SQLAlchemyError("Database error")

    mock_delete.side_effect = mock_delete_side_effect

    auth: Tuple[User, UserToken] = (user, test_user_token)
    response = await logout.logout_user(Response(), auth, test_db)

    assert_sqalchemy_error_response(
        response,
        mock_logger_error,
        "Logout failed",
    )


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.delete")
async def test_unexpected_error_during_logout_direct(
    mock_delete: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test unexpected error during logout via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    async def mock_delete_side_effect(*args: Any, **kwargs: Any) -> None:
        raise Exception("Unexpected error")

    mock_delete.side_effect = mock_delete_side_effect

    auth: Tuple[User, UserToken] = (user, test_user_token)
    response = await logout.logout_user(Response(), auth, test_db)

    assert_exception_error_response(response, mock_logger_error, "Logout failed")


if __name__ == "__main__":
    pytest.main([__file__])
