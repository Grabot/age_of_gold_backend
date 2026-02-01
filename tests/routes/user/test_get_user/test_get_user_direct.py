"""Test for get user endpoint via direct function call."""

from typing import Any, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.user import get_user
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_user_self_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful get user self via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    response: dict[str, Any] = await get_user.get_user(
        get_user_request=None, user_and_token=auth, db=test_db
    )

    assert response["success"] is True
    assert "data" in response
    assert "id" in response["data"]
    assert response["data"]["id"] == test_user.id
    assert response["data"]["username"] == test_user.username


@pytest.mark.asyncio
async def test_successful_get_user_other_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful get other user via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user, _ = await add_token(1001, 1001, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    get_user_request = get_user.GetUserRequest(user_id=other_user.id)

    response: dict[str, Any] = await get_user.get_user(get_user_request, auth, test_db)

    assert response["success"] is True
    assert response["data"]["id"] == other_user.id
    assert response["data"]["username"] == other_user.username


@pytest.mark.asyncio
async def test_get_user_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get user with non-existent user via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    get_user_request = get_user.GetUserRequest(user_id=999999)

    response: dict[str, Any] = await get_user.get_user(get_user_request, auth, test_db)

    assert response["success"] is False
