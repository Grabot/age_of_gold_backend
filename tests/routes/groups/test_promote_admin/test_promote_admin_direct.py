"""Test for promote admin endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, promote_admin, add_group_member
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_promote_to_admin_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful promotion to admin via direct function call."""
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
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
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

    # Promote friend1 to admin
    promote_request = promote_admin.PromoteAdminRequest(
        group_id=group_id, user_id=friend1.id, is_admin=True
    )

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit:
        response = await promote_admin.promote_admin(
            promote_request, admin_auth, test_db
        )

    assert response["success"] is True
    mock_emit.assert_awaited()


@pytest.mark.asyncio
async def test_successful_demote_from_admin_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful demotion from admin via direct function call."""
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
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
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

    # Promote friend1 to admin first
    promote_request = promote_admin.PromoteAdminRequest(
        group_id=group_id, user_id=friend1.id, is_admin=True
    )
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await promote_admin.promote_admin(promote_request, admin_auth, test_db)

    # Demote friend1 from admin
    demote_request = promote_admin.PromoteAdminRequest(
        group_id=group_id, user_id=friend1.id, is_admin=False
    )

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit:
        response = await promote_admin.promote_admin(
            demote_request, admin_auth, test_db
        )

    assert response["success"] is True
    mock_emit.assert_awaited()


@pytest.mark.asyncio
async def test_promote_admin_not_admin_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test promote admin by non-admin via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    # Create friends
    friend1 = await add_user("friend1", 1001, test_db)
    friend2 = await add_user("friend2", 1002, test_db)
    assert friend1.id is not None
    assert friend2.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)
    _, friend2_token = await add_token(1000, 1000, test_db, friend2.id)

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)
    friend1_auth: Tuple[User, UserToken] = (friend1, friend1_token)
    friend2_auth: Tuple[User, UserToken] = (friend2, friend2_token)

    # Add and accept friends
    for friend_auth in [friend1_auth, friend2_auth]:
        add_request = add_friend.AddFriendRequest(user_id=friend_auth[0].id)
        with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
            await add_friend.add_friend(add_request, admin_auth, test_db)

        respond_request = respond_friend_request.RespondFriendRequest(
            friend_id=admin_user.id, accept=True
        )
        with patch(
            "src.api.api_v1.friends.respond_friend_request.sio.emit",
            new_callable=AsyncMock,
        ):
            await respond_friend_request.respond_friend_request(
                respond_request, friend_auth, test_db
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

    # Add friend2 to group
    add_member_request = add_group_member.AddGroupMemberRequest(
        group_id=group_id, user_add_id=friend2.id
    )
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await add_group_member.add_group_member(add_member_request, admin_auth, test_db)

    # Try to promote friend2 as friend1 (non-admin)
    promote_request = promote_admin.PromoteAdminRequest(
        group_id=group_id, user_id=friend2.id, is_admin=True
    )

    with pytest.raises(HTTPException) as exc_info:
        await promote_admin.promote_admin(promote_request, friend1_auth, test_db)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Only group admins can change admin status" in exc_info.value.detail


@pytest.mark.asyncio
async def test_promote_admin_group_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test promote admin in non-existent group via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

    # Try to promote admin in non-existent group
    promote_request = promote_admin.PromoteAdminRequest(
        group_id=99999, user_id=1, is_admin=True
    )

    with pytest.raises(HTTPException) as exc_info:
        await promote_admin.promote_admin(promote_request, admin_auth, test_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Promoting admin failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_promote_admin_user_not_in_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test promote user who is not in the group via direct function call."""
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

    # Create a user who is not in the group
    non_member = await add_user("nonmember", 1003, test_db)
    assert non_member.id is not None

    # Try to promote non-member to admin
    promote_request = promote_admin.PromoteAdminRequest(
        group_id=group_id, user_id=non_member.id, is_admin=True
    )

    with pytest.raises(HTTPException) as exc_info:
        await promote_admin.promote_admin(promote_request, admin_auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "User is not in the group" in exc_info.value.detail
