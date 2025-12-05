"""Test for reset password endpoint via direct function call."""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.settings import reset_password
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_reset_password_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful reset password via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    test_user_password_hash = test_user.password_hash
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    new_password = "new_password"
    reset_password_request = reset_password.ResetPasswordRequest(
        new_password=new_password
    )
    response_json: dict[str, Any] = await reset_password.reset_password(
        reset_password_request, auth, test_db
    )

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.id == test_user_id
    assert test_user_result.password_hash != test_user_password_hash
    password_with_salt = new_password + test_user.salt
    assert test_user.verify_password(test_user_result.password_hash, password_with_salt)
