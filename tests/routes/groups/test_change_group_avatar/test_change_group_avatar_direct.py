"""Test for change group avatar endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import add_friend, respond_friend_request
from src.api.api_v1.groups import change_group_avatar, create_group
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user, generate_unique_username


@pytest.mark.asyncio
async def test_successful_change_group_avatar_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful change group avatar via direct function call."""
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

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()
    mock_request.app.state.cipher.encrypt = MagicMock(
        return_value=b"fake_encrypted_data"
    )

    # Create mock avatar file
    mock_avatar = MagicMock()
    mock_avatar.size = 1024  # 1KB
    mock_avatar.filename = "avatar.png"
    mock_avatar.read = AsyncMock(return_value=b"fake_image_data")

    with patch(
        "src.api.api_v1.groups.change_group_avatar.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await change_group_avatar.change_group_avatar(
            request=mock_request,
            group_id=group_id,
            avatar=mock_avatar,
            user_and_token=admin_auth,
            db=test_db,
        )

    assert response["success"] is True
    mock_emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_successful_remove_group_avatar_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful remove group avatar via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

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
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    group_id = create_response["data"]

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Remove avatar (no avatar file provided)
    with patch(
        "src.api.api_v1.groups.change_group_avatar.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await change_group_avatar.change_group_avatar(
            request=mock_request,
            group_id=group_id,
            avatar=None,
            user_and_token=admin_auth,
            db=test_db,
        )

    assert response["success"] is True
    mock_emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_group_avatar_not_admin_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test change group avatar by non-admin via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    # Create friend
    friend1 = await add_user(generate_unique_username("friend1"), 1001, test_db)
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

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Create mock avatar file
    mock_avatar = MagicMock()
    mock_avatar.size = 1024
    mock_avatar.filename = "avatar.png"
    mock_avatar.read = AsyncMock(return_value=b"fake_image_data")

    # Try to change avatar as non-admin
    with pytest.raises(Exception):  # scalar_one raises NoResultFound for non-admin
        await change_group_avatar.change_group_avatar(
            request=mock_request,
            group_id=group_id,
            avatar=mock_avatar,
            user_and_token=friend1_auth,
            db=test_db,
        )


@pytest.mark.asyncio
async def test_change_group_avatar_invalid_file_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test change group avatar with invalid file via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

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
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    group_id = create_response["data"]

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Create mock avatar file with invalid extension
    mock_avatar = MagicMock()
    mock_avatar.size = 1024
    mock_avatar.filename = "avatar.gif"
    mock_avatar.read = AsyncMock(return_value=b"fake_image_data")

    # Try to change avatar with invalid file type
    with pytest.raises(HTTPException) as exc_info:
        await change_group_avatar.change_group_avatar(
            request=mock_request,
            group_id=group_id,
            avatar=mock_avatar,
            user_and_token=admin_auth,
            db=test_db,
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only PNG/JPG allowed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_change_group_avatar_too_large_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test change group avatar with file too large via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth: Tuple[User, UserToken] = (admin_user, admin_token)

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
        create_response = await create_group.create_group(
            create_request, admin_auth, test_db
        )

    group_id = create_response["data"]

    # Create a mock request with app state
    mock_request = MagicMock()
    mock_request.app.state.s3 = MagicMock()
    mock_request.app.state.cipher = MagicMock()

    # Create mock avatar file that is too large (>2MB)
    mock_avatar = MagicMock()
    mock_avatar.size = 3 * 1024 * 1024  # 3MB
    mock_avatar.filename = "avatar.png"
    mock_avatar.read = AsyncMock(return_value=b"fake_image_data")

    # Try to change avatar with file too large
    with pytest.raises(HTTPException) as exc_info:
        await change_group_avatar.change_group_avatar(
            request=mock_request,
            group_id=group_id,
            avatar=mock_avatar,
            user_and_token=admin_auth,
            db=test_db,
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Avatar too large" in exc_info.value.detail
