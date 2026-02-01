"""Testing fixtures."""

import time
from typing import AsyncGenerator, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker  # type: ignore[attr-defined]
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from main import app
from src.database import get_db
from src.models import User
from src.models.user import hash_email
from src.models.user_token import UserToken
from src.util.util import get_random_colour, hash_password

ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    ASYNC_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

ASYNC_TESTING_SESSION_LOCAL = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


@pytest_asyncio.fixture(scope="module")
async def test_setup() -> AsyncGenerator[TestClient, None]:
    """Create a SQLAlchemy engine and TestClient for tests."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    app.state.s3 = MagicMock()
    app.state.cipher = MagicMock()

    async with ASYNC_TESTING_SESSION_LOCAL() as session:
        password = "testpassword"
        salt = "salt"
        password_with_salt = password + salt
        password_hash = hash_password(password=password_with_salt)
        email_hash = hash_email("testuser@example.com")
        user = User(
            id=1,
            username="testuser",
            email_hash=email_hash,
            password_hash=password_hash,
            salt=salt,
            origin=0,
            colour=get_random_colour()
        )
        session.add(user)
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with ASYNC_TESTING_SESSION_LOCAL() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    try:
        yield client
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await engine.dispose()
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Fixture that creates a token and overrides get_db with the current session."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:

        async def get_db_override() -> AsyncGenerator[AsyncSession, None]:
            yield db

        app.dependency_overrides[get_db] = get_db_override
        yield db
        app.dependency_overrides.pop(get_db, None)


async def add_user(
    username: str,
    origin: int,
    test_db_for_user: AsyncSession,
    email_domain: str = "example.com",
    full_email: str | None = None,
) -> User:
    """Helper function to add a user to the database."""
    password = "testpassword"
    salt = "salt"
    password_with_salt = password + salt
    password_hash = hash_password(password=password_with_salt)
    if not full_email:
        email_hash = hash_email(f"{username}@{email_domain}")
    else:
        email_hash = hash_email(full_email)
    user = User(
        username=username,
        email_hash=email_hash,
        password_hash=password_hash,
        salt=salt,
        origin=origin,
        colour=get_random_colour()
    )
    test_db_for_user.add(user)
    await test_db_for_user.commit()
    return user


async def add_token(
    add_access_expiration: int,
    add_refresh_expiration: int,
    test_db_for_token: AsyncSession,
    id_user: int | None = None,
) -> Tuple[User, UserToken]:
    """Helper function to add a token to the database."""
    user_id = 1
    if id_user:
        user_id = id_user
    user: Optional[User] = await test_db_for_token.get(User, user_id)
    assert user is not None
    user_token = UserToken(
        user_id=user_id,
        access_token=user.generate_auth_token(),
        token_expiration=int(time.time()) + add_access_expiration,
        refresh_token=user.generate_refresh_token(),
        refresh_token_expiration=int(time.time()) + add_refresh_expiration,
    )
    test_db_for_token.add(user_token)
    await test_db_for_token.commit()
    return user, user_token


@pytest_asyncio.fixture
async def mock_tokens() -> AsyncGenerator[tuple[str, str, MagicMock, MagicMock], None]:
    """Fixture that sets up mock tokens for authentication tests."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"

    with (
        patch("src.models.User.generate_auth_token") as mock_generate_auth_token,
        patch("src.models.User.generate_refresh_token") as mock_generate_refresh_token,
    ):
        mock_generate_auth_token.return_value = expected_access_token
        mock_generate_refresh_token.return_value = expected_refresh_token

        yield (
            expected_access_token,
            expected_refresh_token,
            mock_generate_auth_token,
            mock_generate_refresh_token,
        )
