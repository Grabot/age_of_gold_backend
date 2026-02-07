"""Test for get group avatar endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_get_group_avatar(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful get group avatar."""
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

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
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
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [friend1.id],
            },
        )

    group_id = create_response.json()["data"]

    # Get group avatar
    with patch(
        "src.util.util.download_image",
        return_value=b"fake_avatar_data",
    ):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/avatar",
            headers=headers,
            json={"group_id": group_id, "get_default": False},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_get_group_avatar_version(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful get group avatar version."""
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
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [],
            },
        )

    group_id = create_response.json()["data"]

    # Get group avatar version
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/avatar/version",
        headers=headers,
        json={"group_id": group_id},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_get_group_avatar_version_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get avatar version for non-existent group."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {test_user_token.access_token}"}

    # Get avatar version for non-existent group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/avatar/version",
        headers=headers,
        json={"group_id": 99999},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_get_group_avatar_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get avatar for non-existent group."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {test_user_token.access_token}"}

    # Try to get avatar for non-existent group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/avatar",
        headers=headers,
        json={"group_id": 99999, "get_default": False},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Group not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_group_avatar_default(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get default group avatar."""
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
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [],
            },
        )

    group_id = create_response.json()["data"]

    # Get default group avatar
    with patch(
        "src.util.util.download_image",
        return_value=b"fake_default_avatar_data",
    ):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/avatar",
            headers=headers,
            json={"group_id": group_id, "get_default": True},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"
