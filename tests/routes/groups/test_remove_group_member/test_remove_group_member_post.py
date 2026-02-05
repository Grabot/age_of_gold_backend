"""Test for remove group member endpoint via post call."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.config.config import settings
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_remove_member_by_admin(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful removal of member by admin."""
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

    # Remove friend1 from group
    with patch(
        "src.api.api_v1.groups.remove_group_member.sio.emit", new_callable=AsyncMock
    ):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/member/remove",
            headers=admin_headers,
            json={"group_id": group_id, "user_remove_id": friend1.id},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_successful_self_removal(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful self-removal from group."""
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

    # Friend1 removes themselves from group
    with patch(
        "src.api.api_v1.groups.remove_group_member.sio.emit", new_callable=AsyncMock
    ):
        response = test_setup.post(
            f"{settings.API_V1_STR}/group/member/remove",
            headers=friend1_headers,
            json={"group_id": group_id, "user_remove_id": friend1.id},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_remove_member_not_admin_not_self(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test removal by non-admin who is not removing themselves."""
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
            json={"group_id": group_id, "user_add_id": friend2.id},
        )

    # Try to remove friend2 as friend1 (non-admin, not self)
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/member/remove",
        headers=friend1_headers,
        json={"group_id": group_id, "user_remove_id": friend2.id},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Only group admins can remove members" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_member_group_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test removal from non-existent group."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)

    admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}

    # Try to remove member from non-existent group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/member/remove",
        headers=admin_headers,
        json={"group_id": 99999, "user_remove_id": 1},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Group not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_member_not_in_group(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test removal of user who is not in the group."""
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

    # Try to remove non-member from group
    response = test_setup.post(
        f"{settings.API_V1_STR}/group/member/remove",
        headers=admin_headers,
        json={"group_id": group_id, "user_remove_id": non_member.id},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User is not in the group" in response.json()["detail"]
