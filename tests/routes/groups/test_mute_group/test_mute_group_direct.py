"""Test for mute group endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, mute_group
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_mute_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful mute group via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create friend
    friend1 = await add_user("friend1", 1001, test_db)
    assert friend1.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    friend1_auth: Tuple[User, UserToken] = (friend1, friend1_token)

    # Add and accept friend
    add_request = add_friend.AddFriendRequest(user_id=friend1.id)
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await add_friend.add_friend(add_request, auth, test_db)

    respond_request = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
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
        create_response = await create_group.create_group(create_request, auth, test_db)

    group_id = create_response["data"]

    # Mute group
    mute_request = mute_group.MuteGroupRequest(
        group_id=group_id, mute=True, mute_duration_hours=24
    )

    response = await mute_group.mute_group(mute_request, auth, test_db)

    assert response["success"] is True


@pytest.mark.asyncio
async def test_successful_unmute_group_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful unmute group via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[],
    )

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(create_request, auth, test_db)

    group_id = create_response["data"]

    # Mute group first
    mute_request = mute_group.MuteGroupRequest(
        group_id=group_id, mute=True, mute_duration_hours=24
    )
    await mute_group.mute_group(mute_request, auth, test_db)

    # Unmute group
    unmute_request = mute_group.MuteGroupRequest(group_id=group_id, mute=False)

    response = await mute_group.mute_group(unmute_request, auth, test_db)

    assert response["success"] is True


@pytest.mark.asyncio
async def test_mute_group_indefinitely_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test mute group indefinitely via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[],
    )

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(create_request, auth, test_db)

    group_id = create_response["data"]

    # Mute group indefinitely (no duration)
    mute_request = mute_group.MuteGroupRequest(group_id=group_id, mute=True)

    response = await mute_group.mute_group(mute_request, auth, test_db)

    assert response["success"] is True


@pytest.mark.asyncio
async def test_mute_group_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test mute non-existent group via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Try to mute non-existent group
    mute_request = mute_group.MuteGroupRequest(group_id=99999, mute=True)

    with pytest.raises(Exception):  # scalar_one raises NoResultFound
        await mute_group.mute_group(mute_request, auth, test_db)
