"""Test for change username endpoint via direct function call."""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.settings import change_username
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_change_username_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful change username via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    test_user_username = test_user.username
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    new_username = "new_username"
    change_username_request = change_username.ChangeUsernameRequest(
        new_username=new_username
    )
    response_json: dict[str, Any] = await change_username.change_username(
        change_username_request, auth, test_db
    )

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.id == test_user_id
    assert test_user_result.username != test_user_username
    assert test_user_result.username == new_username
