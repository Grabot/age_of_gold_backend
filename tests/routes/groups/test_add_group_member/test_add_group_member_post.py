"""Test for add group member endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user, generate_unique_username


@pytest.mark.asyncio
async def test_successful_add_group_member(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful add group member with valid token."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    friend1 = await add_user(generate_unique_username("friend1"), 1001, test_db)
    new_member = await add_user(generate_unique_username("newmember"), 1002, test_db)
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

    group_id = create_response.json()["data"]

    # Add new member
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/member/add",
            headers=admin_headers,
            json={"group_id": group_id, "user_add_id": new_member.id},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_add_member_not_admin(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test add member by non-admin."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    regular_user = await add_user(generate_unique_username("regular"), 1003, test_db)
    _, regular_token = await add_token(1000, 1000, test_db, regular_user.id)

    friend1 = await add_user(generate_unique_username("friend1"), 1004, test_db)
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}
    regular_headers = {"Authorization": f"Bearer {regular_token.access_token}"}
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

    group_id = create_response.json()["data"]

    # Try to add member as non-admin
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/member/add",
        headers=regular_headers,
        json={"group_id": group_id, "user_add_id": 9999},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Only group admins can add members" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_member_already_in_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test add member who is already in group."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    friend1 = await add_user(generate_unique_username("friend1"), 1005, test_db)
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

    group_id = create_response.json()["data"]

    # Try to add friend1 who is already in the group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/member/add",
        headers=admin_headers,
        json={"group_id": group_id, "user_add_id": friend1.id},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User is already in the group" in response.json()["detail"]
