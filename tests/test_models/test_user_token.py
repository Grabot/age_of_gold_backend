"""Test file for the user token model."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

import time
from typing import Any, Generator, Optional

import pytest
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

from src.models import User, UserToken  # pylint: disable=C0413
from src.util.util import get_user_tokens  # pylint: disable=C0413
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest.mark.asyncio
async def test_token_expiration_expired(test_setup: Generator[Any, Any, Any]) -> None:
    """Test that a token is correctly identified as expired"""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_token = UserToken(
            user_id=1,
            access_token="access_token",
            token_expiration=int(time.time()) - 1000,
            refresh_token="refresh_token",
            refresh_token_expiration=int(time.time()) - 1000,
        )
        db.add(user_token)
        await db.commit()
        await db.refresh(user_token)

        assert user_token.refresh_is_expired() is True
        await db.delete(user_token)
        await db.commit()
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_token_expiration_good(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test that a token is correctly identified as not expired"""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user_token = UserToken(
            user_id=1,
            access_token="access_token",
            token_expiration=int(time.time()) + 1000,
            refresh_token="refresh_token",
            refresh_token_expiration=int(time.time()) + 1000,
        )
        db.add(user_token)
        await db.commit()
        await db.refresh(user_token)

        assert user_token.user_id == 1
        assert user_token.access_token == "access_token"
        assert user_token.token_expiration > int(time.time())
        assert user_token.refresh_token == "refresh_token"
        assert user_token.refresh_token_expiration > int(time.time())
        await db.delete(user_token)
        await db.commit()
        assert await db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_user_token_reference(
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test that the user token correctly references the user and vice versa"""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        statement: Select = (
            select(User).where(User.id == 1).options(joinedload(User.tokens))
        )
        result = await db.execute(statement)
        user: Optional[User] = result.unique().scalar_one()
        assert user is not None
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        await db.refresh(user_token)
        await db.refresh(user)

        assert user_token.user_id == user.id
        user_ref = user_token.user
        assert user_ref == user

        user_token_ref = user.tokens
        assert len(user_token_ref) == 1
        assert user_token_ref == [user_token]
        await db.delete(user_token)
        await db.commit()
        assert await db.get(UserToken, user_token.id) is None


if __name__ == "__main__":
    pytest.main([__file__])
