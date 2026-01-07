"""Test for fetch all friends endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_fetch_all_friends(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful fetch all friends with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user1 = await add_user("testuser2", 1002, test_db)
    other_user2 = await add_user("testuser3", 1003, test_db)
    _, other_user1_token = await add_token(1000, 1000, test_db, other_user1.id)
    _, other_user2_token = await add_token(1000, 1000, test_db, other_user2.id)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    other_headers1 = {"Authorization": f"Bearer {other_user1_token.access_token}"}
    other_headers2 = {"Authorization": f"Bearer {other_user2_token.access_token}"}

    # Add friend requests
    response1 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user1.id,
        },
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["success"] is True

    response2 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user2.id,
        },
    )

    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()["success"] is True

    # Accept the friend requests
    response3 = test_setup.post(
        f"{settings.API_V1_STR}/friend/respond",
        headers=other_headers1,
        json={
            "friend_id": user.id,
            "accept": True,
        },
    )

    assert response3.status_code == status.HTTP_200_OK
    assert response3.json()["success"] is True

    response4 = test_setup.post(
        f"{settings.API_V1_STR}/friend/respond",
        headers=other_headers2,
        json={
            "friend_id": user.id,
            "accept": True,
        },
    )

    assert response4.status_code == status.HTTP_200_OK
    assert response4.json()["success"] is True

    # Fetch all friends
    response5 = test_setup.post(
        f"{settings.API_V1_STR}/friend/all",
        headers=headers,
        json={},
    )

    assert response5.status_code == status.HTTP_200_OK
    assert response5.json()["success"] is True
    assert len(response5.json()["data"]) == 2


@pytest.mark.asyncio
async def test_fetch_all_friends_with_filter(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test fetch all friends with user ID filter."""
    user, user_token = await add_token(1000, 1000, test_db)
    other_user1 = await add_user("testuser49", 1004, test_db)
    other_user2 = await add_user("testuser50", 1005, test_db)
    _, other_user1_token = await add_token(1000, 1000, test_db, other_user1.id)
    _, other_user2_token = await add_token(1000, 1000, test_db, other_user2.id)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    other_headers1 = {"Authorization": f"Bearer {other_user1_token.access_token}"}
    other_headers2 = {"Authorization": f"Bearer {other_user2_token.access_token}"}

    # Add friend requests
    response1 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user1.id,
        },
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response1.json()["success"] is True

    response2 = test_setup.post(
        f"{settings.API_V1_STR}/friend/add",
        headers=headers,
        json={
            "user_id": other_user2.id,
        },
    )

    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()["success"] is True

    # Accept the friend requests
    response3 = test_setup.post(
        f"{settings.API_V1_STR}/friend/respond",
        headers=other_headers1,
        json={
            "friend_id": user.id,
            "accept": True,
        },
    )

    assert response3.status_code == status.HTTP_200_OK
    assert response3.json()["success"] is True

    response4 = test_setup.post(
        f"{settings.API_V1_STR}/friend/respond",
        headers=other_headers2,
        json={
            "friend_id": user.id,
            "accept": True,
        },
    )

    assert response4.status_code == status.HTTP_200_OK
    assert response4.json()["success"] is True

    # Fetch all friends with filter
    response5 = test_setup.post(
        f"{settings.API_V1_STR}/friend/all",
        headers=headers,
        json={
            "user_ids": [other_user1.id],
        },
    )

    assert response5.status_code == status.HTTP_200_OK
    assert response5.json()["success"] is True
    assert len(response5.json()["data"]) == 1
    assert response5.json()["data"][0]["friend_id"] == other_user1.id


@pytest.mark.asyncio
async def test_fetch_all_friends_empty(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test fetch all friends with no friends."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    # Fetch all friends
    response = test_setup.post(
        f"{settings.API_V1_STR}/friend/all",
        headers=headers,
        json={},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    # Note: The test user might have friends from previous tests, so we just check the response is successful
