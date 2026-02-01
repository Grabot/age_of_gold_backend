"""Test for get group avatar endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, get_group_avatar
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_get_group_avatar_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful get group avatar via direct function call."""
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
        create_response = await create_group.create_group(create_request, auth, test_db)

    group_id = create_response["data"]

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Get group avatar
    avatar_request = get_group_avatar.GroupAvatarRequest(
        group_id=group_id, get_default=False
    )

    # Mock the download_image function to return fake data
    with patch(
        "src.util.util.download_image",
        return_value=b"fake_avatar_data",
    ):
        response = await get_group_avatar.get_group_avatar(
            request=mock_request,
            group_avatar_request=avatar_request,
            user_and_token=auth,
            db=test_db,
        )

    assert response is not None


@pytest.mark.asyncio
async def test_get_group_avatar_version_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful get group avatar version via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Create group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(create_request, auth, test_db)

    group_id = create_response["data"]

    # Get group avatar version
    version_request = get_group_avatar.GroupAvatarVersionRequest(group_id=group_id)

    response = await get_group_avatar.get_group_avatar_version(
        group_avatar_version_request=version_request,
        user_and_token=auth,
        db=test_db,
    )

    assert response["success"] is True
    assert "data" in response
    assert isinstance(response["data"], int)


@pytest.mark.asyncio
async def test_get_group_avatar_version_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test get avatar version for non-existent group via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Get avatar version for non-existent group
    version_request = get_group_avatar.GroupAvatarVersionRequest(group_id=99999)

    response = await get_group_avatar.get_group_avatar_version(
        group_avatar_version_request=version_request,
        user_and_token=auth,
        db=test_db,
    )

    assert response["success"] is False


@pytest.mark.asyncio
async def test_get_group_avatar_not_found_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test get avatar for non-existent group via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Try to get avatar for non-existent group
    avatar_request = get_group_avatar.GroupAvatarRequest(
        group_id=99999, get_default=False
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_group_avatar.get_group_avatar(
            request=mock_request,
            group_avatar_request=avatar_request,
            user_and_token=auth,
            db=test_db,
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Group not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_group_avatar_default_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test get default group avatar via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Create group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        create_response = await create_group.create_group(create_request, auth, test_db)

    group_id = create_response["data"]

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Get default group avatar
    avatar_request = get_group_avatar.GroupAvatarRequest(
        group_id=group_id, get_default=True
    )

    # Mock the download_image function to return fake data
    with patch(
        "src.util.util.download_image",
        return_value=b"fake_default_avatar_data",
    ):
        response = await get_group_avatar.get_group_avatar(
            request=mock_request,
            group_avatar_request=avatar_request,
            user_and_token=auth,
            db=test_db,
        )

    assert response is not None
