"""Test file for util."""

# ruff: noqa: E402, F401, F811
import sys
import time
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

from src.models import User, UserToken  # pylint: disable=C0413
from src.util.security import (  # pylint: disable=C0413
    check_token,
    decode_token,
)
from src.util.util import (  # pylint: disable=C0413
    delete_user_token_and_return,
    get_failed_response,
    get_user_tokens,
    hash_password,
    refresh_user_token,
)


def test_get_failed_response() -> None:
    """Test the get_failed_response function."""
    response = Response()
    result = get_failed_response("Test message", response)
    assert result == {
        "result": False,
        "message": "Test message",
    }
    assert response.status_code == status.HTTP_400_BAD_REQUEST


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
async def test_check_token(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the check_token function."""
    user: Optional[User] = await test_db.get(User, 1)
    assert user is not None
    user_token = get_user_tokens(user)
    test_db.add(user_token)
    await test_db.commit()
    user_test1, _ = await check_token(test_db, user_token.access_token, "access")
    assert user_test1 == user
    user_test2, _ = await check_token(test_db, "invalid_token", "access")
    assert user_test2 is None
    await test_db.delete(user_token)
    await test_db.commit()
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_delete_user_token_and_return(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the delete_user_token_and_return function."""
    user: Optional[User] = await test_db.get(User, 1)
    assert user is not None
    user_token = get_user_tokens(user)
    test_db.add(user_token)
    await test_db.commit()
    assert await delete_user_token_and_return(test_db, user_token, user) == user
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_refresh_user_token(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test the refresh_user_token function."""
    user: Optional[User] = await test_db.get(User, 1)
    assert user is not None
    user_token = get_user_tokens(user)
    test_db.add(user_token)
    await test_db.commit()
    assert (
        await refresh_user_token(
            test_db, user_token.access_token, user_token.refresh_token
        )
        == user
    )
    assert await refresh_user_token(test_db, "invalid_token", "invalid_token") is None
    assert await test_db.get(UserToken, user_token.id) is None


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


if __name__ == "__main__":
    pytest.main([__file__])
