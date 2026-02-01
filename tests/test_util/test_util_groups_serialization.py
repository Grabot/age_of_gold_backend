"""Test for util.py groups serialization."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.group import Group
from src.util.util import get_successful_login_response
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_get_successful_login_response_with_groups(
    test_setup: any, test_db: AsyncSession
) -> None:
    """Test get_successful_login_response with groups serialization."""
    user, user_token = await add_token(1000, 1000, test_db)
    assert user.id is not None

    # Add some groups to the user
    group1 = Group(
        user_id=user.id,
        group_id=1,
        unread_messages=0,
        mute=False,
        last_message_read_id=0,
        group_version=1,
    )
    group2 = Group(
        user_id=user.id,
        group_id=2,
        unread_messages=5,
        mute=True,
        last_message_read_id=10,
        group_version=3,
    )

    test_db.add_all([group1, group2])
    await test_db.commit()

    # Refresh user to load relationships
    await test_db.refresh(user, ["groups"])

    # Call the function
    response = await get_successful_login_response(user_token, user, test_db)

    assert response["success"] is True
    assert "data" in response
    data = response["data"]

    # Check that groups are serialized correctly
    assert "groups" in data
    groups = data["groups"]
    assert len(groups) == 2

    # Check group data structure
    for group in groups:
        assert "group_id" in group
        assert "group_version" in group
        assert isinstance(group["group_id"], int)
        assert isinstance(group["group_version"], int)

    # Check that specific group data is present
    group_ids = [group["group_id"] for group in groups]
    assert 1 in group_ids
    assert 2 in group_ids
