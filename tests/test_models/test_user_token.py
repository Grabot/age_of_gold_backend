"""Test file for the user token model."""

# ruff: noqa: E402, F401, F811
import sys
import time
from pathlib import Path
from typing import Any, Generator, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

from src.models import User, UserToken  # pylint: disable=C0413
from src.util.util import get_user_tokens  # pylint: disable=C0413


@pytest.mark.asyncio
async def test_token_expiration_expired(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test that a token is correctly identified as expired"""
    user_token = UserToken(
        user_id=1,
        access_token="access_token",
        token_expiration=int(time.time()) - 1000,
        refresh_token="refresh_token",
        refresh_token_expiration=int(time.time()) - 1000,
    )
    test_db.add(user_token)
    await test_db.commit()
    await test_db.refresh(user_token)

    assert user_token.refresh_is_expired() is True
    await test_db.delete(user_token)
    await test_db.commit()
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_token_expiration_good(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test that a token is correctly identified as not expired"""
    user_token = UserToken(
        user_id=1,
        access_token="access_token",
        token_expiration=int(time.time()) + 1000,
        refresh_token="refresh_token",
        refresh_token_expiration=int(time.time()) + 1000,
    )
    test_db.add(user_token)
    await test_db.commit()
    await test_db.refresh(user_token)

    assert user_token.user_id == 1
    assert user_token.access_token == "access_token"
    assert user_token.token_expiration > int(time.time())
    assert user_token.refresh_token == "refresh_token"
    assert user_token.refresh_token_expiration > int(time.time())
    await test_db.delete(user_token)
    await test_db.commit()
    assert await test_db.get(UserToken, user_token.id) is None


@pytest.mark.asyncio
async def test_user_token_reference(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test that the user token correctly references the user and vice versa"""
    statement: Select = (
        select(User).where(User.id == 1).options(joinedload(User.tokens))
    )
    result = await test_db.execute(statement)
    user: Optional[User] = result.unique().scalar_one()
    assert user is not None
    user_token = get_user_tokens(user)
    test_db.add(user_token)
    await test_db.commit()
    await test_db.refresh(user_token)
    await test_db.refresh(user)

    assert user_token.user_id == user.id
    user_ref = user_token.user
    assert user_ref == user

    user_token_ref = user.tokens
    assert len(user_token_ref) == 1
    assert user_token_ref == [user_token]
    await test_db.delete(user_token)
    await test_db.commit()
    assert await test_db.get(UserToken, user_token.id) is None


if __name__ == "__main__":
    pytest.main([__file__])
