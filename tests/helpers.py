"""Helper class for the test."""

# ruff: noqa: E402
from typing import Any
from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def assert_integrity_error_response(
    response: dict[str, Any],
    mock_logger_error: MagicMock,
) -> None:
    """Helper function to assert common integrity error responses."""
    assert_error_response(
        response,
        mock_logger_error,
        IntegrityError,
        "Database constraint violation",
        "Database integrity error: %s",
    )


def assert_sqalchemy_error_response(
    response: dict[str, Any],
    mock_logger_error: MagicMock,
    response_message: str = "Database constraint violation",
) -> None:
    """Helper function to assert common sqlalchemy error responses."""
    assert_error_response(
        response,
        mock_logger_error,
        SQLAlchemyError,
        response_message,
        "Database error: %s",
    )


def assert_exception_error_response(
    response: dict[str, Any],
    mock_logger_error: MagicMock,
    response_message: str = "Database constraint violation",
) -> None:
    """Helper function to assert common sqlalchemy error responses."""
    assert_error_response(
        response, mock_logger_error, Exception, response_message, "Unexpected error: %s"
    )


def assert_error_response(
    response: dict[str, Any],
    mock_logger_error: MagicMock,
    intance_type: type,
    response_message: str = "Database constraint violation",
    error_message: str = "Database integrity error: %s",
) -> None:
    """Helper function to assert error responses."""
    assert response["result"] is False
    assert response["message"] == response_message
    mock_logger_error.assert_called_once()
    args, _ = mock_logger_error.call_args
    assert args[0] == error_message
    assert isinstance(args[1], intance_type)
