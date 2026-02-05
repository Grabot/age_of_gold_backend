"""Test for mute group endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_mute_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful mute group."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    friend1 = await add_user("friend1", 1001, test_db)
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    headers = {"Authorization": f"Bearer {test_user_token.access_token}"}
    friend1_headers = {"Authorization": f"Bearer {friend1_token.access_token}"}

    # Add and accept friend
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/add",
            headers=headers,
            json={"user_id": friend1.id},
        )

    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/respond",
            headers=friend1_headers,
            json={"friend_id": test_user.id, "accept": True},
        )

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "group_name": "Test Group",
                "group_description": "A test group",
                "group_colour": "#FF5733",
                "friend_ids": [friend1.id],
            },
        )

    group_id = create_response.json()["data"]

    # Mute group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/mute",
        headers=headers,
        json={"group_id": group_id, "mute": True, "mute_duration_hours": 24},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_successful_unmute_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful unmute group."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {test_user_token.access_token}"}

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "group_name": "Test Group",
                "group_description": "A test group",
                "group_colour": "#FF5733",
                "friend_ids": [],
            },
        )

    group_id = create_response.json()["data"]

    # Mute group first
    test_setup.post(
        f"{settings.API_V1_STR}/group/mute",
        headers=headers,
        json={"group_id": group_id, "mute": True, "mute_duration_hours": 24},
    )

    # Unmute group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/mute",
        headers=headers,
        json={"group_id": group_id, "mute": False},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_mute_group_indefinitely(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test mute group indefinitely."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {test_user_token.access_token}"}

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "group_name": "Test Group",
                "group_description": "A test group",
                "group_colour": "#FF5733",
                "friend_ids": [],
            },
        )

    group_id = create_response.json()["data"]

    # Mute group indefinitely (no duration)
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/mute",
        headers=headers,
        json={"group_id": group_id, "mute": True},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_mute_group_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test mute non-existent group."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {test_user_token.access_token}"}

    # Try to mute non-existent group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/mute",
        headers=headers,
        json={"group_id": 99999, "mute": True},
    )

    # scalar_one raises NoResultFound which gets handled as 500 or similar
    assert response.status_code != status.HTTP_200_OK
