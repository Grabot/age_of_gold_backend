"""Test for change group avatar endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user, generate_unique_username


@pytest.mark.asyncio
async def test_successful_change_group_avatar(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful change group avatar."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    friend1 = await add_user("friend1", 1001, test_db)
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}
    friend1_headers = {"Authorization": f"Bearer {friend1_token.access_token}"}

    # Add and accept friend
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/add",
            headers=admin_headers,
            json={"user_id": friend1.id},
        )

    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/respond",
            headers=friend1_headers,
            json={"friend_id": admin_user.id, "accept": True},
        )

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=admin_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [friend1.id],
            },
        )

    chat_id = create_response.json()["data"]

    # Change group avatar
    with patch(
        "src.api.api_v1.groups.change_group_avatar.sio.emit", new_callable=AsyncMock
    ):
        response = test_setup.patch(
            f"{settings.API_V1_STR}/group/avatar",
            headers=admin_headers,
            data={"chat_id": chat_id},
            files={"avatar": ("avatar.png", b"fake_image_data", "image/png")},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_successful_remove_group_avatar(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful remove group avatar."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=admin_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [],
            },
        )

    chat_id = create_response.json()["data"]

    # Remove group avatar (no file)
    with patch(
        "src.api.api_v1.groups.change_group_avatar.sio.emit", new_callable=AsyncMock
    ):
        response = test_setup.patch(
            f"{settings.API_V1_STR}/group/avatar",
            headers=admin_headers,
            data={"chat_id": chat_id},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_change_group_avatar_not_admin(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test change group avatar by non-admin."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    friend1 = await add_user(generate_unique_username("friend1"), 1001, test_db)
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}
    friend1_headers = {"Authorization": f"Bearer {friend1_token.access_token}"}

    # Add and accept friend
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/add",
            headers=admin_headers,
            json={"user_id": friend1.id},
        )

    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        test_setup.post(
            f"{settings.API_V1_STR}/friend/respond",
            headers=friend1_headers,
            json={"friend_id": admin_user.id, "accept": True},
        )

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=admin_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [friend1.id],
            },
        )

    chat_id = create_response.json()["data"]

    # Try to change avatar as non-admin
    response = test_setup.patch(
        f"{settings.API_V1_STR}/group/avatar",
        headers=friend1_headers,
        data={"chat_id": chat_id},
        files={"avatar": ("avatar.png", b"fake_image_data", "image/png")},
    )

    # Should fail because non-admin can't access the group
    assert response.status_code != status.HTTP_200_OK


@pytest.mark.asyncio
async def test_change_group_avatar_invalid_file(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test change group avatar with invalid file type."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=admin_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [],
            },
        )

    chat_id = create_response.json()["data"]

    # Try to change avatar with invalid file type
    response = test_setup.patch(
        f"{settings.API_V1_STR}/group/avatar",
        headers=admin_headers,
        data={"chat_id": chat_id},
        files={"avatar": ("avatar.gif", b"fake_image_data", "image/gif")},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only PNG/JPG allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_group_avatar_too_large(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test change group avatar with file too large."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}

    # Create group
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=admin_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
                "colour": "#FF5733",
                "friend_ids": [],
            },
        )

    chat_id = create_response.json()["data"]

    # Create large file data (>2MB)
    large_data = b"x" * (3 * 1024 * 1024)  # 3MB

    # Try to change avatar with file too large
    response = test_setup.patch(
        f"{settings.API_V1_STR}/group/avatar",
        headers=admin_headers,
        data={"chat_id": chat_id},
        files={"avatar": ("avatar.png", large_data, "image/png")},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Avatar too large" in response.json()["detail"]
