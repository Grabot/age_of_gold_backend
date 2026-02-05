"""Test for update group endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_update_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful update group."""
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
                "group_name": "Test Group",
                "group_description": "A test group",
                "group_colour": "#FF5733",
                "friend_ids": [friend1.id],
            },
        )

    group_id = create_response.json()["data"]

    # Update group
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/update",
            headers=admin_headers,
            json={
                "group_id": group_id,
                "group_name": "Updated Group Name",
                "group_description": "Updated description",
                "group_colour": "#0000FF",
            },
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_update_group_not_admin(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test update group by non-admin."""
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
                "group_name": "Test Group",
                "group_description": "A test group",
                "group_colour": "#FF5733",
                "friend_ids": [friend1.id],
            },
        )

    group_id = create_response.json()["data"]

    # Try to update group as non-admin
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/update",
        headers=friend1_headers,
        json={
            "group_id": group_id,
            "group_name": "Updated Group Name",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Only group admins can update group details" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_group_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test update non-existent group."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {admin_token.access_token}"}

    # Try to update non-existent group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/update",
        headers=headers,
        json={
            "group_id": 99999,
            "group_name": "Updated Group Name",
        },
    )

    # scalar_one raises NoResultFound which gets handled as 500 or similar
    assert response.status_code != status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_group_partial_fields(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test update group with only some fields."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {admin_token.access_token}"}

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

    # Update only group name
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/update",
            headers=headers,
            json={
                "group_id": group_id,
                "group_name": "Updated Group Name",
            },
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
