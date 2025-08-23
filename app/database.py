from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (  # pyright: ignore[reportMissingImports]
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.config.config import settings

engine = create_async_engine(settings.ASYNC_DB_URL, echo=False, future=True)
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = async_session()
    try:
        yield db
    finally:
        await db.close()
