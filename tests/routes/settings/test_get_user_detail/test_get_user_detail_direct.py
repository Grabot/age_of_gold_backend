"""Test for get user detail endpoint via direct function call."""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.settings import get_user_detail
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_user_detail_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful get user detail via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    response_json: dict[str, Any] = await get_user_detail.get_user_detail(auth, test_db)

    assert response_json["success"]
    assert "data" in response_json
    assert "user" in response_json["data"]
    assert response_json["data"]["user"]["id"] == test_user.id
    assert response_json["data"]["user"]["username"] == test_user.username
