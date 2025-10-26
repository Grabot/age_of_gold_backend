"""Test for login endpoint via direct post call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from main import app  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_successful_login_with_username_post(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test successful login with username using POST request."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token

    response = test_setup.post(
        "/api/v1.0/login", json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["result"] is True
    assert response_json["access_token"] == expected_access_token
    assert response_json["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_successful_login_with_email_post(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test successful login with email using POST request."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token

    response = test_setup.post(
        "/api/v1.0/login",
        json={"email": "testuser@example.com", "password": "testpassword"},
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["result"] is True
    assert response_json["access_token"] == expected_access_token
    assert response_json["refresh_token"] == expected_refresh_token


@pytest.mark.asyncio
async def test_invalid_request_missing_password_post(
    test_setup: TestClient,
) -> None:
    """Test invalid request with missing password using POST request."""
    response = test_setup.post(
        "/api/v1.0/login", json={"username": "testuser", "password": ""}
    )
    assert response.status_code == 400
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Invalid request"


@pytest.mark.asyncio
async def test_invalid_request_missing_email_and_username_post(
    test_setup: TestClient,
) -> None:
    """Test invalid request with missing email and username using POST request."""
    response = test_setup.post("/api/v1.0/login", json={"password": "testpassword"})
    assert response.status_code == 400
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Invalid request"


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_invalid_email_or_username_post(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test invalid email or username using POST request."""
    response = test_setup.post(
        "/api/v1.0/login",
        json={"email": "nonexistent@example.com", "password": "testpassword"},
    )
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
async def test_invalid_password_post(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test invalid password using POST request."""
    response = test_setup.post(
        "/api/v1.0/login",
        json={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Invalid email/username or password"


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.database.get_db")
async def test_database_error_during_login_post(
    mock_get_db: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test database error during login using POST request."""
    mock_get_db.side_effect = SQLAlchemyError("Database error")
    response = test_setup.post(
        "/api/v1.0/login", json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 500
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Login failed"


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.database.get_db")
async def test_unexpected_error_during_login_post(
    mock_get_db: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test unexpected error during login using POST request."""
    mock_get_db.side_effect = Exception("Unexpected error")
    response = test_setup.post(
        "/api/v1.0/login", json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 500
    response_json = response.json()
    assert response_json["result"] is False
    assert response_json["message"] == "Login failed"


if __name__ == "__main__":
    pytest.main([__file__])
