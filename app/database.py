from asyncio import current_task
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker  # type: ignore[attr-defined]
from sqlalchemy.ext.asyncio import (  # pylint: disable=redefined-builtin
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config.config import settings

engine_async = create_async_engine(
    settings.ASYNC_DB_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_pre_ping=settings.POOL_PRE_PING,
    pool_recycle=settings.POOL_RECYCLE,
    echo=settings.DEBUG,
)

async_session = async_scoped_session(
    async_sessionmaker(
        bind=engine_async,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    ),
    scopefunc=current_task,
)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
