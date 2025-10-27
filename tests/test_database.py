"""Test file for database."""

# ruff: noqa: E402
import sys
from pathlib import Path
from typing import Any, Generator
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def mock_settings() -> Generator[Any, Any, Any]:
    """Mock the settings for database configuration."""
    with patch("src.config.config.settings") as mock_settings:  # pylint: disable=W0621
        mock_settings.ASYNC_DB_URL = "sqlite+aiosqlite:///:memory:"
        mock_settings.POOL_SIZE = 5
        mock_settings.MAX_OVERFLOW = 10
        mock_settings.POOL_PRE_PING = True
        mock_settings.POOL_RECYCLE = 3600
        mock_settings.DEBUG = False

        import importlib  # pylint: disable=C0415

        import src.database  # pylint: disable=C0415

        importlib.reload(src.database)

        yield


@pytest.mark.asyncio
async def test_engine_creation() -> None:
    """Test the creation of the database engine."""
    from src.database import engine_async  # pylint: disable=C0415

    assert engine_async.pool.size() == 5  # type: ignore[attr-defined]
    assert engine_async.pool._max_overflow == 10  # type: ignore[attr-defined]
    assert engine_async.pool._pre_ping is True  # type: ignore[attr-defined]
    assert engine_async.pool._recycle == 3600  # type: ignore[attr-defined]
    assert str(engine_async.url) == "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_get_db() -> None:
    """Test the get_db function."""
    from src.database import get_db  # pylint: disable=C0415

    async for session in get_db():
        assert isinstance(session, AsyncSession)
        assert session.is_active


if __name__ == "__main__":
    pytest.main([__file__])
