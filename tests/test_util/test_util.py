"""Test file for util."""

import time
from typing import Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, UserToken
from src.util.util import (
    delete_user_token_and_return,
    get_user_tokens,
    hash_password,
    refresh_user_token,
)
from tests.conftest import add_token


def test_hash_password() -> None:
    """Test the hash_password function."""
    password = "test_password"
    hashed_password = hash_password(password)
    assert hashed_password != password
    assert hashed_password.startswith("$argon2")


def test_get_user_tokens_with_none_user_id() -> None:
    """Test the get_user_tokens function with a user that has no ID."""
    user = User(
        id=None,
        username="test_user",
        password_hash="not_important",
        email_hash="not_important",
        salt="salt",
        origin=0,
    )
    with pytest.raises(ValueError, match="User ID should not be None"):
        get_user_tokens(user)


@pytest.mark.asyncio
async def test_get_user_tokens(
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the get_user_tokens function."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens
    user: Optional[User] = await test_db.get(User, 1)
    assert user is not None
    user_token = get_user_tokens(user)
    assert user_token.user_id == user.id
    assert user_token.access_token == expected_access_token
    assert user_token.refresh_token == expected_refresh_token
    assert user_token.token_expiration > int(time.time())
    assert user_token.refresh_token_expiration > int(time.time())


@pytest.mark.asyncio
async def test_delete_user_token_and_return(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the delete_user_token_and_return function."""
    user, user_token = await add_token(1000, 1000, test_db)
    assert user is not None
    assert await delete_user_token_and_return(test_db, user_token, user) == user
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_refresh_user_token(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the refresh_user_token function."""
    user, user_token = await add_token(1000, 1000, test_db)
    assert user is not None
    assert (
        await refresh_user_token(
            test_db, user_token.access_token, user_token.refresh_token
        )
        == user
    )
    assert await refresh_user_token(test_db, "invalid_token", "invalid_token") is None
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_refresh_user_token_with_none_user_result(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the refresh_user_token function with a None user result."""
    user: Optional[User] = await test_db.get(User, 1)
    assert user is not None

    user_token = get_user_tokens(user)
    user_token.user_id = 9999
    test_db.add(user_token)
    await test_db.commit()

    assert (
        await refresh_user_token(
            test_db, user_token.access_token, user_token.refresh_token
        )
        is None
    )
    assert await test_db.get(UserToken, user_token.id) is None
