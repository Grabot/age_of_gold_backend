"""Test for add group member endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, add_group_member
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user, generate_unique_username


@pytest.mark.asyncio
async def test_successful_add_group_member_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful add group member via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    # Create friends
    friend1 = await add_user(generate_unique_username("friend1"), 1001, test_db)
    new_member = await add_user(generate_unique_username("newmember"), 1002, test_db)
    assert friend1.id is not None
    assert new_member.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)
    _, _ = await add_token(1000, 1000, test_db, new_member.id)

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
        name="Test Group",
        description="A test group",
        colour="#FF5733",
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

    # Add new member to group
    add_member_request = add_group_member.AddGroupMemberRequest(
        group_id=group_id, user_add_id=new_member.id
    )

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit:
        response = await add_group_member.add_group_member(
            add_member_request, admin_auth, test_db
        )

    assert response["success"] is True
    mock_emit.assert_awaited()


@pytest.mark.asyncio
async def test_add_member_not_admin_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test add member by non-admin via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    regular_user, regular_token = (
        await add_user(generate_unique_username("regular"), 1003, test_db),
        None,
    )
    assert admin_user.id is not None
    assert regular_user.id is not None
    _, regular_token = await add_token(1000, 1000, test_db, regular_user.id)

    friend1 = await add_user(generate_unique_username("friend1"), 1004, test_db)
    assert friend1.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)
    regular_auth: Tuple[User, UserToken] = (regular_user, regular_token)
    friend1_auth: Tuple[User, UserToken] = (friend1, friend1_token)

    # Add and accept friends
    add_request = add_friend.AddFriendRequest(user_id=friend1.id)
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
            respond_request, friend1_auth, test_db
        )

    # Create group
    create_request = create_group.CreateGroupRequest(
        name="Test Group",
        description="A test group",
        colour="#FF5733",
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

    # Try to add member as non-admin
    add_member_request = add_group_member.AddGroupMemberRequest(
        group_id=group_id, user_add_id=9999
    )

    with pytest.raises(HTTPException) as exc_info:
        await add_group_member.add_group_member(
            add_member_request, regular_auth, test_db
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Only group admins can add members" in exc_info.value.detail


@pytest.mark.asyncio
async def test_add_member_already_in_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test add member who is already in group via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    friend1 = await add_user(generate_unique_username("friend1"), 1005, test_db)
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
        name="Test Group",
        description="A test group",
        colour="#FF5733",
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

    # Try to add friend1 who is already in the group
    add_member_request = add_group_member.AddGroupMemberRequest(
        group_id=group_id, user_add_id=friend1.id
    )

    with pytest.raises(HTTPException) as exc_info:
        await add_group_member.add_group_member(add_member_request, admin_auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "User is already in the group" in exc_info.value.detail


@pytest.mark.asyncio
async def test_add_member_group_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test add member to non-existent group via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

    # Try to add member to non-existent group
    add_member_request = add_group_member.AddGroupMemberRequest(
        group_id=99999, user_add_id=1
    )

    with pytest.raises(HTTPException) as exc_info:
        await add_group_member.add_group_member(add_member_request, admin_auth, test_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Adding group member failed" in exc_info.value.detail
