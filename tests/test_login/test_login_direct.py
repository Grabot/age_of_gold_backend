# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from sqlalchemy.exc import SQLAlchemyError

from app.api.api_v1.authorization.login import LoginRequest, login_user
from tests.test_login.conftest_login import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_successful_login_with_username_direct(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(username="testuser", password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_successful_login_with_email_direct(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(
            email="testuser@example.com", password="testpassword"
        )

        response = await login_user(login_request, Response(), db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
async def test_invalid_request_missing_password_direct(
    test_setup: MagicMock,
) -> None:
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(username="testuser", password="")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_request_missing_email_and_username_direct(
    test_setup: MagicMock,
) -> None:
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid request"


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_invalid_email_or_username_direct(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(
            email="nonexistent@example.com", password="testpassword"
        )

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_invalid_password_direct(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(username="testuser", password="wrongpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
@patch("app.database.get_db")
async def test_database_error_during_login_direct(
    mock_get_db: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    mock_get_db.side_effect = SQLAlchemyError("Database error")
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(username="testuser", password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
@patch("app.database.get_db")
async def test_unexpected_error_during_login_direct(
    mock_get_db: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    mock_get_db.side_effect = Exception("Unexpected error")
    async with AsyncTestingSessionLocal() as db:
        login_request = LoginRequest(username="testuser", password="testpassword")

        response = await login_user(login_request, Response(), db)

        assert response["result"] is False
        assert response["message"] == "Internal server error"


if __name__ == "__main__":
    pytest.main([__file__])
