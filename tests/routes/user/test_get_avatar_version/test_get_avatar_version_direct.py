"""Test for get avatar version endpoint via direct function call."""

from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.user import get_avatar
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_avatar_version_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful get avatar version via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    other_user, _ = await add_token(1001, 1001, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    avatar_version_request = get_avatar.AvatarVersionRequest(user_id=other_user.id)

    response = await get_avatar.get_avatar_version(
        avatar_version_request, auth, test_db
    )

    assert response["success"] is True
    assert response["data"] == other_user.avatar_version


@pytest.mark.asyncio
async def test_get_avatar_version_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get avatar version with non-existent user via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    avatar_version_request = get_avatar.AvatarVersionRequest(user_id=999999)

    response = await get_avatar.get_avatar_version(
        avatar_version_request, auth, test_db
    )

    assert response["success"] is False
