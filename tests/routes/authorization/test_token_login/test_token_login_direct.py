"""Test for token login endpoint via direct function call."""

from typing import Any, Tuple
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.authorization import token_login
from src.models.user import User
from src.models.user_token import UserToken
from src.util.util import SuccessfulLoginResponse
from tests.conftest import add_token
from tests.helpers import (
    assert_exception_error_response,
    assert_integrity_error_response,
    assert_sqalchemy_error_response,
    assert_successful_login_dict_key,
)
import time


@pytest.mark.asyncio
async def test_successful_token_login_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful token login via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (user, test_user_token)
    response_dict: SuccessfulLoginResponse = await token_login.login_token_user(
        auth, test_db
    )

    assert_successful_login_dict_key(response_dict)


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

    with pytest.raises(HTTPException) as exc_info:
        await token_login.login_token_user(auth, test_db)

    assert_sqalchemy_error_response(
        exc_info.value,
        mock_logger_error,
        "Token login failed",
    )


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_integrity_error_during_token_login_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test integrity error during token login via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError(
            "Integrity error", params=None, orig=Exception("Database error")
        )

    mock_commit.side_effect = mock_commit_side_effect

    auth: Tuple[User, UserToken] = (user, test_user_token)
    with pytest.raises(HTTPException) as exc_info:
        await token_login.login_token_user(auth, test_db)

    assert_integrity_error_response(
        exc_info.value,
        mock_logger_error,
    )


@pytest.mark.asyncio
@patch("src.database.get_db")
@patch("src.util.gold_logging.logger.error")
@patch("sqlalchemy.ext.asyncio.AsyncSession.commit")
async def test_unexpected_error_during_token_login_direct(
    mock_commit: MagicMock,
    mock_logger_error: MagicMock,
    mock_get_db: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test unexpected error during token login via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    async def mock_commit_side_effect(*args: Any, **kwargs: Any) -> None:
        raise Exception("Unexpected error")

    mock_commit.side_effect = mock_commit_side_effect

    auth: Tuple[User, UserToken] = (user, test_user_token)
    with pytest.raises(HTTPException) as exc_info:
        await token_login.login_token_user(auth, test_db)

    assert_exception_error_response(
        exc_info.value,
        mock_logger_error,
        "Token login failed",
    )


@pytest.mark.asyncio
@patch("src.api.api_v1.authorization.token_login.get_user_tokens")
async def test_tokens_assigned_correctly_during_token_login_direct(
    mock_get_user_tokens: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test old token overwritten with new token values."""
    user, test_user_token = await add_token(1000, 1000, test_db)

    new_token = UserToken(
        user_id=1,
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_expiration=int(time.time()) + 100,
        refresh_token_expiration=int(time.time()) + 100,
    )

    mock_get_user_tokens.return_value = new_token

    auth: Tuple[User, UserToken] = (user, test_user_token)
    response_dict: SuccessfulLoginResponse = await token_login.login_token_user(
        auth, test_db
    )

    assert test_user_token.access_token == new_token.access_token
    assert test_user_token.refresh_token == new_token.refresh_token
    assert test_user_token.token_expiration == new_token.token_expiration
    assert (
        test_user_token.refresh_token_expiration == new_token.refresh_token_expiration
    )

    assert_successful_login_dict_key(response_dict)
