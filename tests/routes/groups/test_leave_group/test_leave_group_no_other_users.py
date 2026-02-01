"""Test for leave group endpoint when no other users in group."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, leave_group
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_leave_group_no_other_users_direct(
    test_setup: any, test_db: AsyncSession
) -> None:
    """Test leaving group when no other users are present via direct function call."""
    admin_user, admin_token = await add_token(1000, 1000, test_db)
    assert admin_user.id is not None

    admin_auth = (admin_user, admin_token)

    # Create group with only admin (no friends)
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

    # Admin leaves group (no other users to notify)
    leave_request = leave_group.LeaveGroupRequest(group_id=group_id)

    with patch(
        "src.api.api_v1.groups.leave_group.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await leave_group.leave_group(leave_request, admin_auth, test_db)

    assert response["success"] is True
    # Should not emit any notifications since no other users
    mock_emit.assert_not_awaited()
