"""File with tests for the decoratory file"""

from typing import Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.decorators import handle_db_errors


@pytest.mark.asyncio
async def test_handle_db_errors_invalid_and_success() -> None:
    """Test handle_db_errors decorator with invalid and successful function calls."""

    @handle_db_errors()
    async def test_func(response: Response, db: AsyncSession) -> Dict[str, str]:
        """Test function that returns a success status."""
        return {"status": "success"}

    result_fail = await test_func(None, None)
    assert result_fail == {"result": False, "message": "Invalid function call"}

    mock_response = MagicMock(spec=Response)
    result_fail_response = await test_func(mock_response, None)
    assert result_fail_response == {"result": False, "message": "Invalid function call"}

    mock_db = AsyncMock(spec=AsyncSession)
    result_success = await test_func(response=mock_response, db=mock_db)
    assert result_success == {"status": "success"}


@pytest.mark.asyncio
async def test_handle_db_errors_integrity_error() -> None:
    """Test handle_db_errors decorator with IntegrityError."""
    mock_response = MagicMock(spec=Response)
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.rollback = AsyncMock()

    @handle_db_errors()
    async def test_func(response: Response, db: AsyncSession) -> None:
        """Test function that raises an IntegrityError."""
        raise IntegrityError("IntegrityError", "params", "orig")

    result = await test_func(response=mock_response, db=mock_db)

    assert result == {"result": False, "message": "Database constraint violation"}
    mock_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_db_errors_sqlalchemy_error() -> None:
    """Test handle_db_errors decorator with SQLAlchemyError."""
    mock_response = MagicMock(spec=Response)
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.rollback = AsyncMock()

    @handle_db_errors()
    async def test_func(response: Response, db: AsyncSession) -> None:
        """Test function that raises an SQLAlchemyError."""
        raise SQLAlchemyError("SQLAlchemyError")

    result = await test_func(response=mock_response, db=mock_db)

    assert result == {"result": False, "message": "Internal server error"}
    mock_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_db_errors_unexpected_error() -> None:
    """Test handle_db_errors decorator with unexpected error."""
    mock_response = MagicMock(spec=Response)
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.rollback = AsyncMock()

    @handle_db_errors()
    async def test_func(response: Response, db: AsyncSession) -> None:
        """Test function that raises an unexpected error."""
        raise Exception("Unexpected error")

    result = await test_func(response=mock_response, db=mock_db)

    assert result == {"result": False, "message": "Internal server error"}
    mock_db.rollback.assert_awaited_once()
