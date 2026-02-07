"""Test for fetch groups endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_fetch_all_groups(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful fetch all groups with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)

    # Create a friend
    friend = await add_user("testfriend1", 1001, test_db)
    _, friend_token = await add_token(1000, 1000, test_db, friend.id)

    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    friend_headers = {"Authorization": f"Bearer {friend_token.access_token}"}

    # Add and accept friend
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/add",
            headers=headers,
            json={"user_id": friend.id},
        )

    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/respond",
            headers=friend_headers,
            json={"friend_id": user.id, "accept": True},
        )

    # Create a group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [friend.id],
            },
        )

    # Fetch all groups
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/all",
        headers=headers,
        json={},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert "data" in response.json()
    assert len(response.json()["data"]) == 1


@pytest.mark.asyncio
async def test_fetch_groups_with_filter(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test fetch groups with group ID filter."""
    user, user_token = await add_token(1000, 1000, test_db)

    friend = await add_user("friend", 1002, test_db)
    _, friend_token = await add_token(1000, 1000, test_db, friend.id)

    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    friend_headers = {"Authorization": f"Bearer {friend_token.access_token}"}

    # Add and accept friend
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/add",
            headers=headers,
            json={"user_id": friend.id},
        )

    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/respond",
            headers=friend_headers,
            json={"friend_id": user.id, "accept": True},
        )

    # Create a group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [friend.id],
            },
        )

    group_id = create_response.json()["data"]

    # Fetch specific group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/all",
        headers=headers,
        json={"group_ids": [group_id]},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["group_id"] == group_id


@pytest.mark.asyncio
async def test_fetch_groups_empty(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test fetch groups when user has no groups."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/group/all",
        headers=headers,
        json={},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert response.json()["data"] == []
