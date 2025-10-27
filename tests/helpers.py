"""Helper class for the test."""

from typing import Any
from unittest.mock import MagicMock

import httpx
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


def assert_successful_response(
    response: httpx.Response,
    status_code: int = 200,
) -> dict[str, Any]:
    """Asserts that the response is successful and returns the response JSON."""
    assert response.status_code == status_code
    response_json: dict[str, Any] = response.json()
    assert response_json["result"] is True
    return response_json


def assert_successful_response_token(
    response: httpx.Response,
    expected_access_token: str,
    expected_refresh_token: str,
    status_code: int = 200,
) -> None:
    """Asserts that the response is successful and contains the expected access and refresh tokens."""
    response_json: dict[str, Any] = assert_successful_response(response, status_code)
    assert response_json["access_token"] == expected_access_token
    assert response_json["refresh_token"] == expected_refresh_token


def assert_successful_response_token_key(
    response: httpx.Response,
    status_code: int = 200,
) -> None:
    """Asserts that the response is successful and contains access and refresh tokens."""
    response_json: dict[str, Any] = assert_successful_response(response, status_code)
    assert "access_token" in response_json
    assert "refresh_token" in response_json
