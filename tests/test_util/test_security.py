"""File with tests for the security file"""

import time
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.user_token import UserToken
from src.util.security import (
    check_token,
    checked_auth_token,
    decode_token,
    get_valid_auth_token,
)
from src.util.util import get_user_tokens
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_get_valid_auth_token_valid() -> None:
    """Test getting a valid authentication token."""
    credentials = MagicMock()
    credentials.credentials = "valid_token"
    token = await get_valid_auth_token(credentials)
    assert token == "valid_token"


@pytest.mark.asyncio
async def test_get_valid_auth_token_invalid() -> None:
    """Test getting an invalid authentication token."""
    credentials = MagicMock()
    credentials.credentials = ""
    with pytest.raises(HTTPException) as exc_info:
        await get_valid_auth_token(credentials)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_check_token(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the check_token function."""
    user, user_token = await add_token(1000, 1000, test_db)
    assert user is not None
    user_test1, _ = await check_token(test_db, user_token.access_token, "access")
    assert user_test1 == user
    user_test2, _ = await check_token(test_db, user_token.refresh_token, "refresh")
    assert user_test2 == user
    user_test3, _ = await check_token(test_db, "invalid_token", "access")
    assert user_test3 is None
    user_test4, _ = await check_token(test_db, "invalid_token", "refresh")
    assert user_test4 is None
    await test_db.delete(user_token)
    await test_db.commit()
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_check_token_not_in_database(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the check_token function without the token in the database."""
    user, user_token = await add_token(1000, 1000, test_db)
    assert user is not None
    await test_db.delete(user_token)
    await test_db.commit()
    user_test1, _ = await check_token(test_db, user_token.access_token, "access")
    assert user_test1 is None


@pytest.mark.asyncio
async def test_check_token_with_expired_token(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the check_token function with an expired token."""
    user: Optional[User] = await test_db.get(User, 1)
    assert user is not None
    user_token = get_user_tokens(user)
    user_token.token_expiration = int(time.time()) - 1
    test_db.add(user_token)
    await test_db.commit()

    user_test, token_test = await check_token(
        test_db, user_token.access_token, "access"
    )
    assert user_test is None
    assert token_test is None
    await test_db.delete(user_token)
    await test_db.commit()
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_token_encode_decode(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the token encode and decode functionality."""
    user: Optional[User] = await test_db.get(User, 1)
    assert user is not None
    user_token = user.generate_auth_token()
    assert decode_token(user_token, "access")


def test_decode_token_invalid_type() -> None:
    """Test decoding a token with an invalid type."""
    with patch("src.util.security.pyjwt.decode") as mock_decode:
        mock_decode.return_value = {"typ": "refresh"}
        result = decode_token("valid_token", "access")
        assert result is False


@pytest.mark.asyncio
async def test_checked_auth_token(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the checked_auth_token function."""
    user, user_token = await add_token(1000, 1000, test_db)
    assert user is not None
    user_test_return, user_token_return = await checked_auth_token(
        user_token.access_token, test_db
    )
    assert user_test_return == user
    assert user_token_return == user_token
