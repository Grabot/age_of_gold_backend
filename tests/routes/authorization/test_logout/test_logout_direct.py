# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

import time
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from fastapi import Response
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from app.api.api_v1.authorization.logout import logout_user
from app.models.user import User
from app.models.user_token import UserToken
from tests.conftest import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
async def test_successful_logout_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user_id = 1
        user = await db.get(User, user_id)
        assert user is not None
        test_user_token = UserToken(
            user_id=user_id,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

        request = MagicMock()
        request.headers.get.return_value = "Bearer test_access_token"

        response = await logout_user(request, Response(), db)

        user_tokens = await db.execute(select(UserToken).where(UserToken.user_id == 1))
        assert user_tokens.scalar() is None

        assert response["result"] is True
        assert response["message"] == "User logged out successfully."


@pytest.mark.asyncio
async def test_logout_with_invalid_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        request = MagicMock()
        request.headers.get.return_value = "Bearer invalid_token"

        response = await logout_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "User not found or token expired"


@pytest.mark.asyncio
async def test_logout_with_missing_token_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        request = MagicMock()
        request.headers.get.return_value = None

        response = await logout_user(request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Authorization token is missing or invalid"


@pytest.mark.asyncio
async def test_database_error_during_login_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user_id = 1
        user = await db.get(User, user_id)
        assert user is not None
        test_user_token = UserToken(
            user_id=user_id,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

        async def mock_delete(*args: Any, **kwargs: Any) -> None:
            raise SQLAlchemyError("Database error")

        db.delete = mock_delete

        request = MagicMock()
        request.headers.get.return_value = "Bearer test_access_token"

        response = await logout_user(request, Response(), db)

        assert not response["result"]
        assert response["message"] == "Internal server error"


@pytest.mark.asyncio
async def test_unexpected_error_during_logout_direct(
    test_setup: Generator[Any, Any, Any],
) -> None:
    async with AsyncTestingSessionLocal() as db:
        user_id = 1
        user = await db.get(User, user_id)
        assert user is not None
        test_user_token = UserToken(
            user_id=user_id,
            access_token="test_access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="test_refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(test_user_token)
        await db.commit()

        async def mock_delete(*args: Any, **kwargs: Any) -> None:
            raise Exception("Unexpected error")

        db.delete = mock_delete

        request = MagicMock()
        request.headers.get.return_value = "Bearer test_access_token"

        response = await logout_user(request, Response(), db)

        assert not response["result"]
        assert response["message"] == "Internal server error"


# @pytest.mark.asyncio
# async def test_logout_with_invalid_token_not_found_direct(
#     test_setup: Generator[Any, Any, Any],
# ) -> None:
#     async with AsyncTestingSessionLocal() as db:
#         user_id = 1
#         user = await db.get(User, user_id)
#         assert user is not None
#         test_user_token = UserToken(
#             user_id=user_id,
#             access_token="test_access_token",
#             token_expiration=int(time.time()) + 1000,
#             refresh_token="test_refresh_token",
#             refresh_token_expiration=int(time.time()) + 1000,
#         )
#         db.add(test_user_token)
#         await db.commit()

#         request = MagicMock()
#         request.headers.get.return_value = "Bearer test_access_token"

#         response = await logout_user(request, Response(), db)

#         assert response["result"] is False
#         assert response["message"] == "Authorization token is missing or invalid"

if __name__ == "__main__":
    pytest.main([__file__])
