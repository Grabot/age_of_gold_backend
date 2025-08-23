# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.test_login.conftest_login import test_setup


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_successful_login_with_username(
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    with TestClient(app) as client:
        expected_access_token = "access_token_test"
        expected_refresh_token = "refresh_token_test"
        mock_generate_auth_token.return_value = expected_access_token
        mock_generate_refresh_token.return_value = expected_refresh_token

        response = client.post(
            "/api/v1.0/login", json={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["result"] is True
        assert response_json["access_token"] == expected_access_token
        assert response_json["refresh_token"] == expected_refresh_token


if __name__ == "__main__":
    pytest.main([__file__])
