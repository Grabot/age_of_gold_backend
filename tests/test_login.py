from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Response
from pytest_mock import MockerFixture

from app.api.api_v1.authorization.login import login_user
from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(mocker: MockerFixture) -> None:
    # Mock the database session
    mock_db = AsyncMock()

    # Mock the response object
    mock_response = MagicMock(spec=Response)

    # Mock the login request
    mock_login_request = MagicMock()
    mock_login_request.username = "testuser"
    mock_login_request.password = "testpassword"

    # Mock the user object
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.password_hash = "hashedpassword"
    mock_user.salt = "salt"
    mock_user.origin = 1
    mock_user.serialize = {"id": 1, "username": "testuser"}

    # Mock the user token
    mock_user_token = MagicMock()
    mock_user_token.access_token = "accesstoken"
    mock_user_token.refresh_token = "refreshtoken"

    # Mock the get_user_tokens function
    mocker.patch("app.util.util.get_user_tokens", return_value=mock_user_token)

    # Call the login_user function
    result = await login_user(mock_login_request, mock_response, mock_db)

    print(f"result: {result}")
    # Assert the result
    assert result == {
        "result": True,
        "message": "user logged in successfully.",
        "access_token": "accesstoken",
        "refresh_token": "refreshtoken",
        "user": {"id": 1, "username": "testuser"},
    }
