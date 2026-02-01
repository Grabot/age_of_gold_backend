"""Test for create group endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_create_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful group creation via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create a friend
    other_user = await add_user("testfriend1", 1001, test_db)
    assert other_user.id is not None
    _, other_user_token = await add_token(1000, 1000, test_db, other_user.id)

    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    other_auth: Tuple[User, UserToken] = (other_user, other_user_token)

    # Add friend request
    add_friend_request = add_friend.AddFriendRequest(user_id=other_user.id)
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        response1 = await add_friend.add_friend(add_friend_request, auth, test_db)
    assert response1["success"] is True

    # Accept friend request
    respond_request = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        response2 = await respond_friend_request.respond_friend_request(
            respond_request, other_auth, test_db
        )
    assert response2["success"] is True

    # Create group
    create_group_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[other_user.id],
    )

    with (
        patch(
            "age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"
        ) as mock_task,
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit,
    ):
        mock_task.return_value = MagicMock()
        response3 = await create_group.create_group(create_group_request, auth, test_db)

    assert response3["success"] is True
    assert "data" in response3
    assert isinstance(response3["data"], int)
    mock_emit.assert_awaited()


@pytest.mark.asyncio
async def test_create_group_not_friends_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test creating group with non-friend via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create a user who is NOT a friend
    other_user = await add_user("testuser2", 1002, test_db)
    assert other_user.id is not None

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Try to create group with non-friend
    create_group_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[other_user.id],
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_group.create_group(create_group_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert f"User {other_user.id} is not your friend" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_group_self_only_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test creating group with only self (no friends) via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Create group with empty friend list (only creator)
    create_group_request = create_group.CreateGroupRequest(
        group_name="Solo Group",
        group_description="A solo test group",
        group_colour="#00FF00",
        friend_ids=[],
    )

    with (
        patch(
            "age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"
        ) as mock_task,
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        mock_task.return_value = MagicMock()
        response = await create_group.create_group(create_group_request, auth, test_db)

    assert response["success"] is True
    assert "data" in response


@pytest.mark.asyncio
async def test_create_group_multiple_friends_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test creating group with multiple friends via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create multiple friends
    friend1 = await add_user("friend1", 1003, test_db)
    friend2 = await add_user("friend2", 1004, test_db)
    assert friend1.id is not None
    assert friend2.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)
    _, friend2_token = await add_token(1000, 1000, test_db, friend2.id)

    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    friend1_auth: Tuple[User, UserToken] = (friend1, friend1_token)
    friend2_auth: Tuple[User, UserToken] = (friend2, friend2_token)

    # Add and accept friend requests
    for friend, friend_auth in [(friend1, friend1_auth), (friend2, friend2_auth)]:
        add_request = add_friend.AddFriendRequest(user_id=friend.id)
        with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
            await add_friend.add_friend(add_request, auth, test_db)

        respond_request = respond_friend_request.RespondFriendRequest(
            friend_id=test_user.id, accept=True
        )
        with patch(
            "src.api.api_v1.friends.respond_friend_request.sio.emit",
            new_callable=AsyncMock,
        ):
            await respond_friend_request.respond_friend_request(
                respond_request, friend_auth, test_db
            )

    # Create group with multiple friends
    create_group_request = create_group.CreateGroupRequest(
        group_name="Multi Friend Group",
        group_description="Group with multiple friends",
        group_colour="#0000FF",
        friend_ids=[friend1.id, friend2.id],
    )

    with (
        patch(
            "age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"
        ) as mock_task,
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit,
    ):
        mock_task.return_value = MagicMock()
        response = await create_group.create_group(create_group_request, auth, test_db)

    assert response["success"] is True
    assert "data" in response
    # Should emit to both friends
    assert mock_emit.await_count == 2


@pytest.mark.asyncio
async def test_create_group_user_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test creating group when user has no ID via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    test_user.id = None  # Simulate user without ID

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    create_group_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[],
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_group.create_group(create_group_request, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Can't find user"
