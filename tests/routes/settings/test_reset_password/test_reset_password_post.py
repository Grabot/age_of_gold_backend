"""Test for reset password endpoint via direct get call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from src.models.user import User
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_reset_password(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful reset password with valid token."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    test_user_password_hash = test_user.password_hash
    new_password = "new_password"
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.patch(
        f"{settings.API_V1_STR}/password/reset",
        headers=headers,
        json={
            "new_password": new_password,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.id == test_user_id
    assert test_user_result.password_hash != test_user_password_hash
    password_with_salt = new_password + test_user.salt
    assert test_user.verify_password(test_user_result.password_hash, password_with_salt)
