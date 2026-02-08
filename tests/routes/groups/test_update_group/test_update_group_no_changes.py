"""Test for update group endpoint when no changes are made."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.friends import add_friend, respond_friend_request
from src.api.api_v1.groups import create_group, update_group
from tests.conftest import add_token, add_user
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_update_group_no_changes_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test updating group with no changes via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    # Create friend
    friend1 = await add_user("friend1", 1001, test_db)
    assert friend1.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)

    admin_auth = (admin_user, admin_token)
    friend1_auth = (friend1, friend1_token)

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

    # Update group with all None values (no changes)
    update_request = update_group.UpdateGroupRequest(
        chat_id=chat_id,
        name=None,
        description=None,
        colour=None,
    )
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock) as mock_emit:
        response = await update_group.update_group(update_request, admin_auth, test_db)

    assert response["success"] is True
    # Should still emit event even if no changes
    mock_emit.assert_awaited()
