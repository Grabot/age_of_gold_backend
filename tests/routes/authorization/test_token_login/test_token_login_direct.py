# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

import time
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select

from app.api.api_v1.authorization.token_login import LoginTokenRequest, login_token_user
from app.models.user import User
from app.models.user_token import UserToken
from tests.conftest import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
async def test_successful_token_login_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        user_token = UserToken(
            user_id=user.id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(user_token)
        await db.commit()

        login_request = LoginTokenRequest(access_token="valid_access_token")

        response = await login_token_user(login_request, Response(), db)

        assert response["result"] is True
        assert response["message"] == "User logged in successfully."
        assert "access_token" in response
        assert "refresh_token" in response
        assert response["user"] == user.serialize


@pytest.mark.asyncio
async def test_invalid_request_no_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginTokenRequest(access_token="")

        response = await login_token_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginTokenRequest(access_token="invalid_access_token")

        response = await login_token_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_database_error_during_token_login_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        user_token = UserToken(
            user_id=user.id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(user_token)
        await db.commit()
        login_request = LoginTokenRequest(access_token="valid_access_token")

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise SQLAlchemyError("Database error")

        db.commit = mock_commit

        response = await login_token_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"


@pytest.mark.asyncio
async def test_integrity_error_during_token_login_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        user_token = UserToken(
            user_id=user.id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(user_token)
        await db.commit()
        login_request = LoginTokenRequest(access_token="valid_access_token")

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise IntegrityError(
                "Integrity error", params=None, orig=Exception("Database error")
            )

        db.commit = mock_commit

        response = await login_token_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"


@pytest.mark.asyncio
@patch("app.database.get_db")
async def test_unexpected_error_during_token_login_direct(
    mock_get_db: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user = await db.get(User, 1)
        user_token = UserToken(
            user_id=user.id,
            access_token="valid_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="valid_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(user_token)
        await db.commit()
        login_request = LoginTokenRequest(access_token="valid_access_token")

        async def mock_commit(*args: Any, **kwargs: Any) -> None:
            raise Exception("Unexpected error")

        db.commit = mock_commit

        response = await login_token_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"


if __name__ == "__main__":
    pytest.main([__file__])
