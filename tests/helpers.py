"""Helper class for the test."""

from typing import Any
from unittest.mock import MagicMock

import httpx
from fakeredis import FakeRedis
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.util.util import SuccessfulLoginResponse, LoginData


class AsyncFakeRedis:
    """Async wrapper for FakeRedis."""

    def __init__(self, sync_redis: FakeRedis):
        self.sync_redis = sync_redis

    async def exists(self, key: str) -> Any:
        """Check if a key exists."""
        return self.sync_redis.exists(key)

    async def setex(self, key: str, ttl: int, value: str) -> Any:
        """Set a key with an expiration time."""
        return self.sync_redis.setex(key, ttl, value)

    async def ttl(self, key: str) -> Any:
        """Get the remaining time to live of a key in seconds."""
        return self.sync_redis.ttl(key)

    async def delete(self, key: str) -> Any:
        """Delete a key."""
        return self.sync_redis.delete(key)


def assert_integrity_error_response(
    response: HTTPException,
    mock_logger_error: MagicMock,
) -> None:
    """Helper function to assert common integrity error responses."""
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.detail == "Database constraint violation"
    assert_error_response(
        mock_logger_error,
        "Database integrity error: %s",
        IntegrityError,
    )


def assert_sqalchemy_error_response(
    response: HTTPException,
    mock_logger_error: MagicMock,
    response_message: str,
) -> None:
    """Helper function to assert common sqlalchemy error responses."""
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.detail == response_message
    assert_error_response(
        mock_logger_error,
        "Database error: %s",
        SQLAlchemyError,
    )


def assert_exception_error_response(
    response: HTTPException,
    mock_logger_error: MagicMock,
    response_message: str,
) -> None:
    """Helper function to assert common sqlalchemy error responses."""
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.detail == response_message
    assert_error_response(mock_logger_error, "Unexpected error: %s", Exception)


def assert_error_response(
    mock_logger_error: MagicMock,
    error_message: str,
    intance_type: type,
) -> None:
    """Helper function to assert error responses."""
    mock_logger_error.assert_called_once()
    args, _ = mock_logger_error.call_args
    assert args[0] == error_message
    assert isinstance(args[1], intance_type)


def assert_successful_login_dict(
    response_dict: SuccessfulLoginResponse,
    expected_access_token: str,
    expected_refresh_token: str,
) -> None:
    """Helper function to assert successful login responses."""
    response_dict_success: LoginData = assert_successful_dict(response_dict)
    assert_successful_login_dict_data(
        response_dict_success, expected_access_token, expected_refresh_token
    )


def assert_successful_login_dict_data(
    response_dict: LoginData,
    expected_access_token: str,
    expected_refresh_token: str,
) -> None:
    """Helper function to assert successful data in login responses."""
    assert response_dict["access_token"] == expected_access_token
    assert response_dict["refresh_token"] == expected_refresh_token
    assert "profile_version" in response_dict
    assert "avatar_version" in response_dict


def assert_successful_login_dict_key(
    response_dict: SuccessfulLoginResponse,
) -> None:
    """Helper function to assert successful login responses only key check."""
    response_dict_success: LoginData = assert_successful_dict(response_dict)
    assert_successful_login_dict_data_key(response_dict_success)


def assert_successful_login_dict_data_key(
    response_dict: LoginData,
) -> None:
    """Helper function to assert successful data in login responses only key check."""
    assert "access_token" in response_dict
    assert "refresh_token" in response_dict
    assert "profile_version" in response_dict
    assert "avatar_version" in response_dict


def assert_successful_login(
    response: httpx.Response,
    expected_access_token: str,
    expected_refresh_token: str,
    status_code: int = status.HTTP_200_OK,
) -> None:
    """Asserts that the response is successful and contains the expected access and refresh tokens."""
    response_dict: LoginData = assert_successful(response, status_code)
    assert_successful_login_dict_data(
        response_dict, expected_access_token, expected_refresh_token
    )


def assert_successful_login_key(
    response: httpx.Response,
) -> None:
    """Asserts that the response is successful and contains access and refresh tokens."""
    response_json: LoginData = assert_successful(response)
    assert_successful_login_dict_data_key(response_json)


def assert_successful_dict(
    response_json: SuccessfulLoginResponse,
) -> LoginData:
    """Asserts that the response is successful and returns the response JSON."""
    assert response_json["success"]
    assert "data" in response_json
    return response_json["data"]


def assert_successful(
    response: httpx.Response, status_code: int = status.HTTP_200_OK
) -> LoginData:
    """Asserts that the response is successful and returns the response JSON."""
    assert response.status_code == status_code
    response_json: SuccessfulLoginResponse = response.json()
    return assert_successful_dict(response_json)
