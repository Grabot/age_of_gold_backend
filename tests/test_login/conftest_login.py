# ruff: noqa: E402
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (  # pyright: ignore[reportMissingImports]
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.database import get_db
from app.models import User
from app.util.util import hash_password
from main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
AsyncTestingSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="module")
def test_setup() -> Generator[Any, Any, Any]:
    async def init_db() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        async with AsyncTestingSessionLocal() as session:
            password = "testpassword"
            salt = "salt"
            password_with_salt = password + salt
            password_hash = hash_password(password=password_with_salt)
            user = User(
                username="testuser",
                email_hash="not_important",
                password_hash=password_hash,
                salt=salt,
                origin=0,
            )
            session.add(user)
            await session.commit()

    asyncio.run(init_db())

    def override_get_db() -> Any:
        async def get_db_override() -> Any:
            async with AsyncTestingSessionLocal() as session:
                yield session

        return get_db_override

    app.dependency_overrides[get_db] = override_get_db()

    with TestClient(app) as c:
        yield c

    # Cleanup
    async def cleanup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await engine.dispose()

    asyncio.run(cleanup())
    app.dependency_overrides.clear()
