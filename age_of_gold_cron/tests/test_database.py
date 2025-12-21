"""Test file for database."""

from typing import Generator
from unittest.mock import patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from age_of_gold_cron.age_of_gold_cron.cron_settings import CronSettings
from pytest_mock import MockerFixture


@pytest.fixture(name="mock_settings")
def mock_settings() -> Generator[None, None, None]:
    """Mock the settings for database configuration."""
    with patch(
        "age_of_gold_cron.age_of_gold_cron.cron_settings.cron_settings"
    ) as mock_cron_settings:
        mock_cron_settings.ASYNC_DB_URL = "sqlite+aiosqlite:///:memory:"
        mock_cron_settings.POOL_SIZE = 5
        mock_cron_settings.MAX_OVERFLOW = 10
        mock_cron_settings.POOL_PRE_PING = True
        mock_cron_settings.POOL_RECYCLE = 3600
        mock_cron_settings.DEBUG = False

        import importlib

        import age_of_gold_cron.age_of_gold_cron.database

        importlib.reload(age_of_gold_cron.age_of_gold_cron.database)

        yield


@pytest.mark.asyncio
async def test_engine_creation(mock_settings: MockerFixture) -> None:
    """Test the creation of the database engine."""
    from age_of_gold_cron.age_of_gold_cron.database import engine_async  # pylint: disable=C0415

    assert engine_async.pool.size() == 5  # type: ignore[attr-defined]
    assert engine_async.pool._max_overflow == 10  # type: ignore[attr-defined]
    assert engine_async.pool._pre_ping is True  # type: ignore[attr-defined]
    assert engine_async.pool._recycle == 3600  # type: ignore[attr-defined]
    assert str(engine_async.url) == "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_get_db(mock_settings: MockerFixture) -> None:
    """Test the get_db function."""
    from age_of_gold_cron.age_of_gold_cron.database import get_db  # pylint: disable=C0415

    async for session in get_db():
        assert isinstance(session, AsyncSession)
        assert session.is_active


def test_async_db_url() -> None:
    """Test that ASYNC_DB_URL is constructed correctly."""
    settings: CronSettings = CronSettings(
        POSTGRES_URL="test-db-url",
        POSTGRES_PORT=5432,
        POSTGRES_USER="test-user",
        POSTGRES_PASSWORD="test-password",
        POSTGRES_DB="test-db",
    )

    expected_url: str = (
        "postgresql+asyncpg://test-user:test-password@test-db-url:5432/test-db"
    )

    assert settings.ASYNC_DB_URL == expected_url
