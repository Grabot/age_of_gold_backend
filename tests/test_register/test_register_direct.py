# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response

from app.api.api_v1.authorization.register import RegisterRequest, register_user
from tests.test_login.conftest_login import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
@patch("app.models.User.generate_auth_token")
@patch("app.models.User.generate_refresh_token")
@patch("app.celery_worker.tasks.task_generate_avatar.delay")
async def test_successful_register_direct(
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with AsyncTestingSessionLocal() as db:
        login_request = RegisterRequest(
            email="new_test@test.test", username="new_test", password="new_testpassword"
        )
        response_object = Response()

        response = await register_user(login_request, response_object, db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token
        mock_task_generate_avatar.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
