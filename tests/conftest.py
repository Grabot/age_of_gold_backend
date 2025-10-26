"""Testing fixtures."""

# ruff: noqa: E402
import time
from typing import AsyncGenerator, Optional, Tuple

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker  # type: ignore[attr-defined]
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from main import app
from src.config.config import settings
from src.database import get_db
from src.models import User
from src.models.user import hash_email
from src.models.user_token import UserToken
from src.util.util import hash_password

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
    # Initialize the database
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create a test user
    async with ASYNC_TESTING_SESSION_LOCAL() as session:
        password = "testpassword"
        salt = "salt"
        password_with_salt = password + salt
        password_hash = hash_password(password=password_with_salt)
        email_hash = hash_email("testuser@example.com", settings.PEPPER)
        user = User(
            id=1,
            username="testuser",
            email_hash=email_hash,
            password_hash=password_hash,
            salt=salt,
            origin=0,
        )
        session.add(user)
        await session.commit()

    # Override the get_db dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with ASYNC_TESTING_SESSION_LOCAL() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Create and yield the TestClient
    client = TestClient(app)
    try:
        yield client
    finally:
        # Cleanup
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


async def add_token(
    add_access_expiration: int,
    add_refresh_expiration: int,
    test_db_for_token: AsyncSession,
) -> Tuple[User, UserToken]:
    """Helper function to add a token to the database."""
    user_id = 1
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
