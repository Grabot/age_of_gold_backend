"""File with tests for the decoratory file"""

from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.decorators import handle_db_errors


@pytest.mark.asyncio
async def test_handle_db_errors_invalid_no_db() -> None:
    """Test handle_db_errors decorator with invalid call from no db."""

    @handle_db_errors()
    async def func_for_test_success(db: None) -> Any:
        """Test function that returns a success status."""

    with pytest.raises(HTTPException) as exc_info:
        await func_for_test_success(db=None)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "Invalid function call"


@pytest.mark.asyncio
async def test_handle_db_errors_success() -> None:
    """Test handle_db_errors decorator with successful function call."""
    mock_db = AsyncMock(spec=AsyncSession)

    @handle_db_errors()
    async def func_for_test_success(db: AsyncSession) -> Dict[str, str]:
        """Test function that returns a success status."""
        return {"status": "success"}

    result_success = await func_for_test_success(db=mock_db)
    assert result_success == {"status": "success"}


@pytest.mark.asyncio
async def test_handle_db_errors_integrity_error() -> None:
    """Test handle_db_errors decorator with IntegrityError."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.rollback = AsyncMock()

    @handle_db_errors()
    async def func_for_test_integrity_error(db: AsyncSession) -> None:
        """Test function that raises an IntegrityError."""
        raise IntegrityError("IntegrityError", "params", "orig")

    with pytest.raises(HTTPException) as exc_info:
        await func_for_test_integrity_error(db=mock_db)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "Database constraint violation"
    mock_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_db_errors_sqlalchemy_error() -> None:
    """Test handle_db_errors decorator with SQLAlchemyError."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.rollback = AsyncMock()

    @handle_db_errors()
    async def func_for_test_sqalchemy_error(db: AsyncSession) -> None:
        """Test function that raises an SQLAlchemyError."""
        raise SQLAlchemyError("SQLAlchemyError")

    with pytest.raises(HTTPException) as exc_info:
        await func_for_test_sqalchemy_error(db=mock_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Internal server error"
    mock_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_db_errors_unexpected_error() -> None:
    """Test handle_db_errors decorator with unexpected error."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.rollback = AsyncMock()

    @handle_db_errors()
    async def func_for_test_unexpected_error(db: AsyncSession) -> None:
        """Test function that raises an unexpected error."""
        raise Exception("Unexpected error")

    with pytest.raises(HTTPException) as exc_info:
        await func_for_test_unexpected_error(db=mock_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Internal server error"
    mock_db.rollback.assert_awaited_once()
