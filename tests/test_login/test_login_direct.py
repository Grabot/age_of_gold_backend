# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response

from app.api.api_v1.authorization.login import LoginRequest, login_user
from tests.test_login.conftest_login import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
async def test_successful_login_with_username(
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
        response_object = Response()
        response_object.status_code = 200

        response = await login_user(login_request, response_object, db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token


if __name__ == "__main__":
    pytest.main([__file__])
