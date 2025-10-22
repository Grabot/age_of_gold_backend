"""Test file for util."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

import jwt as pyjwt
import time
from typing import Any, Dict, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response, status

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

from src.config.config import settings  # pylint: disable=C0413
from src.models import User, UserToken  # pylint: disable=C0413
from src.util.util import (  # pylint: disable=C0413
    check_token,
    delete_user_token_and_return,
    get_auth_token,
    get_failed_response,
    get_user_tokens,
    hash_password,
    refresh_user_token,
)
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


def test_get_failed_response() -> None:
    """Test the get_failed_response function."""
    response = Response()
    result = get_failed_response("Test message", response)
    assert result == {
        "result": False,
        "message": "Test message",
    }
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_auth_token() -> None:
    """Test the get_auth_token function."""
    auth_header = "Bearer test_token"
    assert get_auth_token(auth_header) == "test_token"
    assert get_auth_token(None) == ""


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
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_get_user_tokens(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test the get_user_tokens function."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None
        user_token = get_user_tokens(user)
        assert user_token.user_id == user.id
        assert user_token.access_token == expected_access_token
        assert user_token.refresh_token == expected_refresh_token
        assert user_token.token_expiration > int(time.time())
        assert user_token.refresh_token_expiration > int(time.time())


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_check_token(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test the check_token function."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        user_test1, _ = await check_token(db, user_token.access_token)
        assert user_test1 == user
        user_test2, _ = await check_token(db, "invalid_token")
        assert user_test2 is None
        await db.delete(user_token)
        await db.commit()
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_delete_user_token_and_return(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test the delete_user_token_and_return function."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        assert await delete_user_token_and_return(db, user_token, user) == user
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_refresh_user_token(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test the refresh_user_token function."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        assert (
            await refresh_user_token(
                db, user_token.access_token, user_token.refresh_token
            )
            == user
        )
        assert await refresh_user_token(db, "invalid_token", "invalid_token") is None
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_check_token_with_expired_token(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test the check_token function with an expired token."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None
        user_token = get_user_tokens(user)
        user_token.token_expiration = int(time.time()) - 1
        db.add(user_token)
        await db.commit()

        user_test, token_test = await check_token(db, user_token.access_token)
        assert user_test is None
        assert token_test is None
        await db.delete(user_token)
        await db.commit()
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_refresh_user_token_with_none_user_result(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test the refresh_user_token function with a None user result."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None

        user_token = get_user_tokens(user)
        user_token.user_id = 9999
        db.add(user_token)
        await db.commit()

        assert (
            await refresh_user_token(
                db, user_token.access_token, user_token.refresh_token
            )
            is None
        )
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("jwt.decode")
async def test_refresh_user_token_with_expired_access_token(
    mock_jwt_decode: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test the refresh_user_token function with an expired access token."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None
        user_token = get_user_tokens(user)
        user_token.token_expiration = int(time.time()) - 1
        db.add(user_token)
        await db.commit()
        mock_jwt_decode.side_effect = [
            {"exp": int(time.time()) + 3600, "id": user.id},
            {"exp": int(time.time()) + 3600, "username": user.username},
        ]
        assert (
            await refresh_user_token(
                db, user_token.access_token, user_token.refresh_token
            )
            == user
        )
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_token_encode_decode() -> None:
    """Test the token encode and decode functionality."""
    payload = {
        "id": 123,
        "iss": "https://test.test",
        "aud": "test/test",
        "sub": "test_sub",
        "exp": int(time.time()) + 1800,
        "iat": int(time.time()),
    }

    headers: Dict[str, str] = {
        "alg": "ES256",
        "kid": "test_kid",
        "typ": "jwt",
    }

    token = pyjwt.encode(
        payload,
        settings.jwt_pem,
        algorithm=headers["alg"],
        headers=headers,
    )

    try:
        decoded_token = pyjwt.decode(
            token,
            settings.jwt_pem,
            algorithms=[headers["alg"]],
            options={"verify_aud": False},
        )
        print("Token is valid:", decoded_token)
    except Exception as e:
        print("Token is invalid:", e)


if __name__ == "__main__":
    pytest.main([__file__])
