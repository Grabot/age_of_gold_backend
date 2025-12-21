"""
Database module for managing asynchronous database connections using SQLAlchemy.
"""

from asyncio import current_task
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker  # type: ignore[attr-defined]
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from age_of_gold_cron.age_of_gold_cron.cron_settings import cron_settings

engine_async = create_async_engine(
    cron_settings.ASYNC_DB_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=cron_settings.POOL_SIZE,
    max_overflow=cron_settings.MAX_OVERFLOW,
    pool_pre_ping=cron_settings.POOL_PRE_PING,
    pool_recycle=cron_settings.POOL_RECYCLE,
    echo=cron_settings.DEBUG,
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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get a database session.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session.
    """
    db = async_session()
    try:
        yield db
    finally:
        await db.close()
