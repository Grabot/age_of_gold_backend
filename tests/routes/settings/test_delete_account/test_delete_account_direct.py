"""Test for delete account endpoint via direct function call."""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.settings import delete_account
from sqlalchemy import select
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_delete_account_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful delete account via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    response_json: dict[str, Any] = await delete_account.delete_account(
        auth, test_db
    )

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is None
    tokens_result = await test_db.execute(
        select(UserToken).where(UserToken.user_id == test_user_id)
    )
    assert tokens_result.scalars().all() == []
