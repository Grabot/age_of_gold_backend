# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

from fastapi.testclient import TestClient

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

import time
from typing import Any, AsyncGenerator, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from app.models import User, UserToken
from app.util.util import get_user_tokens
from tests.conftest import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
async def test_token_expiration_expired(test_setup: Generator[Any, Any, Any]) -> None:
    async with AsyncTestingSessionLocal() as db:
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
    async with AsyncTestingSessionLocal() as db:
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
    async with AsyncTestingSessionLocal() as db:
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
