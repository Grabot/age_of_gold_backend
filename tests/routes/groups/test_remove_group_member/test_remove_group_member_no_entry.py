"""Test for remove group member endpoint when group entry doesn't exist."""

from unittest.mock import AsyncMock, patch

from sqlalchemy.sql.selectable import Select
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.friends import add_friend, respond_friend_request
from src.api.api_v1.groups import create_group, remove_group_member
from src.models.group import Group
from tests.conftest import add_token, add_user
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_remove_group_member_no_entry_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test removing group member when group entry doesn't exist via direct function call."""
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

    # Manually delete the group entry for friend1 to simulate missing entry
    group_statement: Select = select(Group).where(
        Group.user_id == friend1.id, Group.chat_id == chat_id
    )
    group_result = await test_db.execute(group_statement)
    group_entry = group_result.first()
    await test_db.delete(group_entry.Group)
    await test_db.commit()

    # Admin tries to remove friend1 (group entry doesn't exist)
    remove_request = remove_group_member.RemoveGroupMemberRequest(
        chat_id=chat_id, user_remove_id=friend1.id
    )

    with patch(
        "src.api.api_v1.groups.remove_group_member.sio.emit", new_callable=AsyncMock
    ) as mock_emit:
        response = await remove_group_member.remove_group_member(
            remove_request, admin_auth, test_db
        )

    assert response["success"] is True
    mock_emit.assert_awaited()
