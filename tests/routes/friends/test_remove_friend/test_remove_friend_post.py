"""Test for remove friend endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_remove_friend(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful remove friend with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    other_headers = {"Authorization": f"Bearer {other_user_token.access_token}"}

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

    # Accept the friend request from the other user's perspective
    response2 = test_setup.post(
        f"{settings.API_V1_STR}/friend/respond",
        headers=other_headers,
        json={
            "friend_id": user.id,
            "accept": True,
        },
    )

    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()["success"] is True

    # Remove the friend
    response3 = test_setup.post(
        f"{settings.API_V1_STR}/friend/remove",
        headers=headers,
        json={
            "friend_id": other_user.id,
        },
    )

    assert response3.status_code == status.HTTP_200_OK
    assert response3.json()["success"] is True


@pytest.mark.asyncio
async def test_remove_friend_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test remove friend with non-existent friend."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/remove",
        headers=headers,
        json={
            "friend_id": 999999,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Friend request not found"


@pytest.mark.asyncio
async def test_remove_friend_not_accepted(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test remove friend with non-accepted friend."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser3", 1003, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    # Add friend request but don't accept it
    response1 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["success"] is True

    # Try to remove the friend (should fail)
    response2 = test_setup.post(
        f"{settings.API_V1_STR}/friend/remove",
        headers=headers,
        json={
            "friend_id": other_user.id,
        },
    )

    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert response2.json()["detail"] == "Can only remove accepted friends"
