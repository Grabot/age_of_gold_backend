# ruff: noqa: E402
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from typing import Any, Generator
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
def mock_settings() -> Generator[Any, Any, Any]:
    with patch("app.config.config.settings") as mock_settings:
        mock_settings.ASYNC_DB_URL = "sqlite+aiosqlite:///:memory:"
        mock_settings.POOL_SIZE = 5
        mock_settings.MAX_OVERFLOW = 10
        mock_settings.POOL_PRE_PING = True
        mock_settings.POOL_RECYCLE = 3600
        mock_settings.DEBUG = False

        import importlib

        import app.database

        importlib.reload(app.database)

        yield


@pytest.mark.asyncio
async def test_engine_creation() -> None:
    from app.database import engine_async

    assert engine_async.pool.size() == 5  # type: ignore
    assert engine_async.pool._max_overflow == 10  # type: ignore
    assert engine_async.pool._pre_ping is True  # type: ignore
    assert engine_async.pool._recycle == 3600  # type: ignore
    assert str(engine_async.url) == "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_get_db() -> None:
    from app.database import get_db

    async with get_db() as session:
        assert isinstance(session, AsyncSession)
        assert session.is_active


if __name__ == "__main__":
    pytest.main([__file__])
