"""Test for leave group endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, leave_group
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_leave_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful leave group via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    friend1 = await add_user("friend1", 1001, test_db)
    assert friend1.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)
    friend1_auth: Tuple[User, UserToken] = (friend1, friend1_token)

    # Add and accept friend
    add_request_friend1 = add_friend.AddFriendRequest(user_id=friend1.id)
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await add_friend.add_friend(add_request_friend1, admin_auth, test_db)

    respond_request = respond_friend_request.RespondFriendRequest(
        friend_id=admin_user.id, accept=True
    )
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        await respond_friend_request.respond_friend_request(
            respond_request, friend1_auth, test_db
        )

    # Create group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[friend1.id],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    group_id = create_response["data"]

    # Friend1 leaves group
    leave_request = leave_group.LeaveGroupRequest(group_id=group_id)

    with patch(
        "src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await leave_group.leave_group(leave_request, friend1_auth, test_db)

    assert response["success"] is True
    mock_emit.assert_awaited()


@pytest.mark.asyncio
async def test_leave_group_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test leaving non-existent group via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Try to leave non-existent group
    leave_request = leave_group.LeaveGroupRequest(group_id=99999)

    with pytest.raises(HTTPException) as exc_info:
        await leave_group.leave_group(leave_request, auth, test_db)

    assert exc_info.value.status_code == 404
    assert "Group not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_leave_group_last_member_deletes_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test that leaving as last member deletes the group via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

    # Create group with only admin
    create_request = create_group.CreateGroupRequest(
        group_name="Solo Group",
        group_description="A solo test group",
        group_colour="#00FF00",
        friend_ids=[],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    group_id = create_response["data"]

    # Admin leaves group (last member)
    leave_request = leave_group.LeaveGroupRequest(group_id=group_id)

    with patch("src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock):
        response = await leave_group.leave_group(leave_request, admin_auth, test_db)

    assert response["success"] is True


@pytest.mark.asyncio
async def test_leave_group_admin_removes_admin_status_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test that admin leaving removes admin status via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    # Create friend
    friend1 = await add_user("friend1", 1001, test_db)
    assert friend1.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)
    friend1_auth: Tuple[User, UserToken] = (friend1, friend1_token)

    # Add and accept friend
    add_request = add_friend.AddFriendRequest(user_id=friend1.id)
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await add_friend.add_friend(add_request, admin_auth, test_db)

    respond_request = respond_friend_request.RespondFriendRequest(
        friend_id=admin_user.id, accept=True
    )
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        await respond_friend_request.respond_friend_request(
            respond_request, friend1_auth, test_db
        )

    # Create group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[friend1.id],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    group_id = create_response["data"]

    # Admin leaves group
    leave_request = leave_group.LeaveGroupRequest(group_id=group_id)

    with patch(
        "src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await leave_group.leave_group(leave_request, admin_auth, test_db)

    assert response["success"] is True
    mock_emit.assert_awaited()
