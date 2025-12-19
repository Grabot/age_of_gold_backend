"""Test for delete account endpoint via direct get call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.config.config import settings
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_delete_account(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful delete account with valid token."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.delete(
        f"{settings.API_V1_STR}/delete/account",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is None
    tokens_result = await test_db.execute(
        select(UserToken).where(UserToken.user_id == test_user_id)
    )
    assert tokens_result.scalars().all() == []
