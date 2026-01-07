"""Test for add friend endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_add_friend(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful add friend with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser1", 1001, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_add_friend_self(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test add friend with self."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": user.id,
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "You can't add yourself"


@pytest.mark.asyncio
async def test_add_friend_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test add friend with non-existent user."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": 999999,
        },
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "No user found."


@pytest.mark.asyncio
async def test_add_friend_already_friends(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test add friend with already friends."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    # First add friend request
    response1 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["success"] is True

    # Second add friend request (should fail)
    response2 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert response2.json()["detail"] == "You are already friends"
