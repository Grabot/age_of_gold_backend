"""Test for create group endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_create_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful group creation with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)

    # Create a friend
    friend = await add_user("testfriend1", 1001, test_db)
    _, friend_token = await add_token(1000, 1000, test_db, friend.id)

    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    friend_headers = {"Authorization": f"Bearer {friend_token.access_token}"}

    # Add friend request
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        response1 = test_setup.post(
            f"{settings.API_V1_STR}/friend/add",
            headers=headers,
            json={"user_id": friend.id},
        )
    assert response1.status_code == status.HTTP_200_OK

    # Accept friend request
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        response2 = test_setup.post(
            f"{settings.API_V1_STR}/friend/respond",
            headers=friend_headers,
            json={"friend_id": user.id, "accept": True},
        )
    assert response2.status_code == status.HTTP_200_OK

    # Create group
    with (
        patch(
            "age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"
        ) as mock_task,
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        mock_task.return_value = MagicMock()
        response3 = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "group_name": "Test Group",
                "group_description": "A test group",
                "group_colour": "#FF5733",
                "friend_ids": [friend.id],
            },
        )

    assert response3.status_code == status.HTTP_200_OK
    assert response3.json()["success"] is True
    assert "data" in response3.json()


@pytest.mark.asyncio
async def test_create_group_not_friends(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test creating group with non-friend."""
    user, user_token = await add_token(1000, 1000, test_db)

    # Create a user who is NOT a friend
    non_friend = await add_user("nonfriend", 1002, test_db)

    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.post(
        f"{settings.API_V1_STR}/group/create",
        headers=headers,
        json={
            "group_name": "Test Group",
            "group_description": "A test group",
            "group_colour": "#FF5733",
            "friend_ids": [non_friend.id],
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"User {non_friend.id} is not your friend" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_group_empty_friends(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test creating group with empty friend list (solo group)."""
    user, user_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    with (
        patch(
            "age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"
        ) as mock_task,
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        mock_task.return_value = MagicMock()
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "group_name": "Solo Group",
                "group_description": "A solo test group",
                "group_colour": "#00FF00",
                "friend_ids": [],
            },
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_create_group_multiple_friends(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test creating group with multiple friends."""
    user, user_token = await add_token(1000, 1000, test_db)

    # Create multiple friends
    friend1 = await add_user("friend1", 1003, test_db)
    friend2 = await add_user("friend2", 1004, test_db)
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)
    _, friend2_token = await add_token(1000, 1000, test_db, friend2.id)

    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    # Add and accept friend requests
    for friend, friend_token_obj in [
        (friend1, friend1_token),
        (friend2, friend2_token),
    ]:
        friend_headers = {"Authorization": f"Bearer {friend_token_obj.access_token}"}

        with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
            test_setup.post(
                f"{settings.API_V1_STR}/friend/add",
                headers=headers,
                json={"user_id": friend.id},
            )

        with patch(
            "src.api.api_v1.friends.respond_friend_request.sio.emit",
            new_callable=AsyncMock,
        ):
            test_setup.post(
                f"{settings.API_V1_STR}/friend/respond",
                headers=friend_headers,
                json={"friend_id": user.id, "accept": True},
            )

    # Create group with multiple friends
    with (
        patch(
            "age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"
        ) as mock_task,
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        mock_task.return_value = MagicMock()
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "group_name": "Multi Friend Group",
                "group_description": "Group with multiple friends",
                "group_colour": "#0000FF",
                "friend_ids": [friend1.id, friend2.id],
            },
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
