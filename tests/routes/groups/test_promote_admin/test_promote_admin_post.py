"""Test for promote admin endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_promote_to_admin(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful promotion to admin."""
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

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
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

    # Promote friend1 to admin
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/admin/promote",
            headers=admin_headers,
            json={"group_id": group_id, "user_id": friend1.id, "is_admin": True},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_successful_demote_from_admin(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful demotion from admin."""
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

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
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

    # Promote friend1 to admin first
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        test_setup.post(
            f"{settings.API_V1_STR}/group/admin/promote",
            headers=admin_headers,
            json={"group_id": group_id, "user_id": friend1.id, "is_admin": True},
        )

    # Demote friend1 from admin
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/admin/promote",
            headers=admin_headers,
            json={"group_id": group_id, "user_id": friend1.id, "is_admin": False},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_promote_admin_not_admin(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test promote admin by non-admin."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    friend1 = await add_user("friend1", 1001, test_db)
    friend2 = await add_user("friend2", 1002, test_db)
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)
    _, friend2_token = await add_token(1000, 1000, test_db, friend2.id)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}
    friend1_headers = {"Authorization": f"Bearer {friend1_token.access_token}"}
    friend2_headers = {"Authorization": f"Bearer {friend2_token.access_token}"}

    # Add and accept friends
    for friend_headers in [friend1_headers, friend2_headers]:
        with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
            test_setup.post(
                f"{settings.API_V1_STR}/friend/add",
                headers=admin_headers,
                json={
                    "user_id": friend1.id
                    if friend_headers == friend1_headers
                    else friend2.id
                },
            )

        with patch(
            "src.api.api_v1.friends.respond_friend_request.sio.emit",
            new_callable=AsyncMock,
        ):
            test_setup.post(
                f"{settings.API_V1_STR}/friend/respond",
                headers=friend_headers,
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

    # Add friend2 to group
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        test_setup.post(
            f"{settings.API_V1_STR}/group/member/add",
            headers=admin_headers,
            json={"group_id": group_id, "user_id": friend2.id},
        )

    # Try to promote friend2 as friend1 (non-admin)
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/admin/promote",
        headers=friend1_headers,
        json={"group_id": group_id, "user_id": friend2.id, "is_admin": True},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Only group admins can change admin status" in response.json()["detail"]


@pytest.mark.asyncio
async def test_promote_admin_group_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test promote admin in non-existent group."""
    _, admin_token = await add_token(1000, 1000, test_db)

    headers = {"Authorization": f"Bearer {admin_token.access_token}"}

    # Try to promote admin in non-existent group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/admin/promote",
        headers=headers,
        json={"group_id": 99999, "user_id": 1, "is_admin": True},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Promoting admin failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_promote_admin_user_not_in_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test promote user who is not in the group."""
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

    # Create a user who is not in the group
    non_member = await add_user("nonmember", 1003, test_db)

    # Try to promote non-member to admin
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/admin/promote",
        headers=admin_headers,
        json={"group_id": group_id, "user_id": non_member.id, "is_admin": True},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User is not in the group" in response.json()["detail"]
