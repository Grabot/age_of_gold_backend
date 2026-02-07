"""Test for get group avatar ClientError handling."""

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.api_v1.groups import create_group, get_group_avatar
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_get_group_avatar_client_error_no_such_key_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test get group avatar with ClientError NoSuchKey via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: tuple[User, UserToken] = (test_user, test_user_token)

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

    # Mock the download_image function to raise ClientError with NoSuchKey
    from botocore.exceptions import ClientError

    mock_client_error = ClientError(
        error_response={"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
        operation_name="get_object",
    )

    with patch(
        "src.util.util.download_image",
        side_effect=mock_client_error,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_group_avatar.get_group_avatar(
                request=mock_request,
                group_avatar_request=avatar_request,
                user_and_token=auth,
                db=test_db,
            )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Avatar not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_group_avatar_client_error_other_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test get group avatar with other ClientError via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    auth: tuple[User, UserToken] = (test_user, test_user_token)

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

    # Mock the download_image function to raise other ClientError
    from botocore.exceptions import ClientError

    mock_client_error = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
        operation_name="get_object",
    )

    with patch(
        "src.util.util.download_image",
        side_effect=mock_client_error,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_group_avatar.get_group_avatar(
                request=mock_request,
                group_avatar_request=avatar_request,
                user_and_token=auth,
                db=test_db,
            )

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to fetch avatar" in exc_info.value.detail
