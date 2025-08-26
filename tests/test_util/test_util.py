# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

import time
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response, status

from app.models import User, UserToken
from app.util.util import (
    check_token,
    delete_user_token_and_return,
    get_auth_token,
    get_failed_response,
    get_user_tokens,
    hash_password,
    refresh_user_token,
)
from tests.conftest import AsyncTestingSessionLocal, test_setup


def test_get_failed_response() -> None:
    response = Response()
    result = get_failed_response("Test message", response)
    assert result == {
        "result": False,
        "message": "Test message",
    }
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_auth_token() -> None:
    auth_header = "Bearer test_token"
    assert get_auth_token(auth_header) == "test_token"
    assert get_auth_token(None) == ""


def test_hash_password() -> None:
    password = "test_password"
    hashed_password = hash_password(password)
    assert hashed_password != password
    assert hashed_password.startswith("$argon2")


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_get_user_tokens(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        user_token = get_user_tokens(user)
        assert user_token.user_id == user.id
        assert user_token.access_token == expected_access_token
        assert user_token.refresh_token == expected_refresh_token
        assert user_token.token_expiration > int(time.time())
        assert user_token.refresh_token_expiration > int(time.time())


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_check_token(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        assert await check_token(db, user_token.access_token) == user
        assert await check_token(db, "invalid_token") is None
        await db.delete(user_token)
        await db.commit()
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_delete_user_token_and_return(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        assert await delete_user_token_and_return(db, user_token, user) == user
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_refresh_user_token(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
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


# TODO: Test generate_auth_token en decoding in `refresh_user_token`?
# Maybe put it in seperate function?


if __name__ == "__main__":
    pytest.main([__file__])
