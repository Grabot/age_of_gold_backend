"""Test for update group endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, update_group
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_update_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful update group via direct function call."""
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

    chat_id = create_response["data"]

    # Update group
    update_request = update_group.UpdateGroupRequest(
        chat_id=chat_id,
        name="Updated Group Name",
        description="Updated description",
        colour="#0000FF",
    )

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit:
        response = await update_group.update_group(update_request, admin_auth, test_db)

    assert response["success"] is True
    mock_emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_group_not_admin_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test update group by non-admin via direct function call."""
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

    chat_id = create_response["data"]

    # Try to update group as non-admin
    update_request = update_group.UpdateGroupRequest(
        chat_id=chat_id,
        name="Updated Group Name",
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_group.update_group(update_request, friend1_auth, test_db)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Only group admins can update group details" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_group_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test update non-existent group via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

    # Try to update non-existent group
    update_request = update_group.UpdateGroupRequest(
        chat_id=99999,
        name="Updated Group Name",
    )

    with pytest.raises(Exception):  # scalar_one raises NoResultFound
        await update_group.update_group(update_request, admin_auth, test_db)


@pytest.mark.asyncio
async def test_update_group_partial_fields_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test update group with only some fields via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

    # Create group
    create_request = create_group.CreateGroupRequest(
        name="Test Group",
        description="A test group",
        colour="#FF5733",
        friend_ids=[],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    chat_id = create_response["data"]

    # Update only group name
    update_request = update_group.UpdateGroupRequest(
        chat_id=chat_id,
        name="Updated Group Name",
    )

    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit:
        response = await update_group.update_group(update_request, admin_auth, test_db)

    assert response["success"] is True
    mock_emit.assert_awaited_once()
