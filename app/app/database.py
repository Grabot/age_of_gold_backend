from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.config import settings

engine = create_async_engine(settings.ASYNC_DB_URL, echo=False, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

engine_sync = create_engine(settings.SYNC_DB_URL, pool_pre_ping=True, pool_size=32, max_overflow=64)


async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()
