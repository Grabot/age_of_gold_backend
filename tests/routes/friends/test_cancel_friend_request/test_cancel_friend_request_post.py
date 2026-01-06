"""Test for cancel friend request endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_cancel_friend_request(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful cancel friend request with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser2", 1002, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    # Add friend request
    response1 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["success"] is True

    # Cancel the friend request
    response2 = test_setup.post(
        f"{settings.API_V1_STR}/friend/cancel",
        headers=headers,
        json={
            "friend_id": other_user.id,
        },
    )

    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()["success"] is True


@pytest.mark.asyncio
async def test_cancel_friend_request_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test cancel friend request with non-existent request."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/cancel",
        headers=headers,
        json={
            "friend_id": 999999,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Friend request not found"


@pytest.mark.asyncio
async def test_cancel_friend_request_not_sent_by_you(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test cancel friend request with request not sent by you."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser3", 1003, test_db)
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    other_headers = {"Authorization": f"Bearer {other_user_token.access_token}"}

    # Add friend request from other user
    response1 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=other_headers,
        json={
            "user_id": user.id,
        },
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["success"] is True

    # Try to cancel the friend request from your perspective (should fail)
    response2 = test_setup.post(
        f"{settings.API_V1_STR}/friend/cancel",
        headers=headers,
        json={
            "friend_id": other_user.id,
        },
    )

    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert response2.json()["detail"] == "You can only cancel requests you have sent"


@pytest.mark.asyncio
async def test_cancel_friend_request_already_accepted(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test cancel friend request with already accepted request."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user = await add_user("testuser43", 1004, test_db)
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    other_headers = {"Authorization": f"Bearer {other_user_token.access_token}"}

    # Add friend request
    response1 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user.id,
        },
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["success"] is True

    # Accept the friend request
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

    # Try to cancel the friend request (should fail)
    response3 = test_setup.post(
        f"{settings.API_V1_STR}/friend/cancel",
        headers=headers,
        json={
            "friend_id": other_user.id,
        },
    )

    assert response3.status_code == status.HTTP_400_BAD_REQUEST
    assert response3.json()["detail"] == "You can only cancel requests you have sent"
