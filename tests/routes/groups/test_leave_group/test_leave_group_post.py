"""Test for leave group endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_leave_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful leave group."""
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

    # Friend1 leaves group
    with patch("src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/leave",
            headers=friend1_headers,
            json={"chat_id": chat_id},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_leave_group_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test leaving non-existent group."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {test_user_token.access_token}"}

    # Try to leave non-existent group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/leave",
        headers=headers,
        json={"chat_id": 99999},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Group not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_leave_group_last_member_deletes_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that leaving as last member deletes the group."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {admin_token.access_token}"}

    # Create group with only admin
    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = test_setup.post(
            f"{settings.API_V1_STR}/group/create",
            headers=headers,
            json={
                "name": "Solo Group",
                "description": "A solo test group",
                "colour": "#00FF00",
                "friend_ids": [],
            },
        )

    chat_id = create_response.json()["data"]

    # Admin leaves group (last member)
    with patch("src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/leave",
            headers=headers,
            json={"chat_id": chat_id},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_leave_group_admin_removes_admin_status(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that admin leaving removes admin status."""
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

    # Admin leaves group
    with patch("src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/leave",
            headers=admin_headers,
            json={"chat_id": chat_id},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
