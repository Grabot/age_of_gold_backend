"""Testing fixtures."""

# ruff: noqa: E402
import sys
from pathlib import Path
from typing import Any, Generator
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker  # type: ignore[attr-defined]
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

sys.path.append(str(Path(__file__).parent.parent))

from src.config.config import settings  # pylint: disable=C0413
from src.database import get_db  # pylint: disable=C0413
from src.models import User  # pylint: disable=C0413
from src.models.user import hash_email  # pylint: disable=C0413
from src.util.util import hash_password  # pylint: disable=C0413
from main import app  # pylint: disable=C0413

ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    ASYNC_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

ASYNC_TESTING_SESSION_LOCAL = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="module")
def test_setup() -> Generator[Any, Any, Any]:
    """Create a SQLAlchemy engine for tests."""

    async def init_db() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
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

    asyncio.run(init_db())

    def override_get_db() -> Any:
        async def get_db_override() -> Any:
            async with ASYNC_TESTING_SESSION_LOCAL() as session:
                yield session

        return get_db_override

    app.dependency_overrides[get_db] = override_get_db()

    with TestClient(app) as c:
        yield c

    async def cleanup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await engine.dispose()

    asyncio.run(cleanup())
    app.dependency_overrides.clear()
