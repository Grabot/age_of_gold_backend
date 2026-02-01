"""Test for fetch groups endpoint via direct function call."""

from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.groups import create_group, fetch_groups
from src.api.api_v1.friends import add_friend, respond_friend_request
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_fetch_all_groups_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful fetch all groups via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create a friend
    friend = await add_user("testfriend1", 1001, test_db)
    assert friend.id is not None
    _, friend_token = await add_token(1000, 1000, test_db, friend.id)

    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    friend_auth: Tuple[User, UserToken] = (friend, friend_token)

    # Add and accept friend
    add_request = add_friend.AddFriendRequest(user_id=friend.id)
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await add_friend.add_friend(add_request, auth, test_db)

    respond_request = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        await respond_friend_request.respond_friend_request(
            respond_request, friend_auth, test_db
        )

    # Create a group
    create_request = create_group.CreateGroupRequest(
        group_name="Test Group",
        group_description="A test group",
        group_colour="#FF5733",
        friend_ids=[friend.id],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        await create_group.create_group(create_request, auth, test_db)

    # Fetch all groups
    fetch_request = fetch_groups.FetchGroupsRequest(group_ids=None)
    response = await fetch_groups.fetch_all_groups(fetch_request, auth, test_db)

    assert response["success"] is True
    assert "data" in response
    assert len(response["data"]) == 1
    assert response["data"][0]["group_name"] == "Test Group"


@pytest.mark.asyncio
async def test_fetch_groups_with_filter_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test fetch groups with group ID filter via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    # Create friends
    friend1 = await add_user("friend1", 1002, test_db)
    friend2 = await add_user("friend2", 1003, test_db)
    assert friend1.id is not None
    assert friend2.id is not None
    _, friend1_token = await add_token(1000, 1000, test_db, friend1.id)
    _, friend2_token = await add_token(1000, 1000, test_db, friend2.id)

    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    friend1_auth: Tuple[User, UserToken] = (friend1, friend1_token)
    friend2_auth: Tuple[User, UserToken] = (friend2, friend2_token)

    # Add and accept friends
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

    # Create two groups
    create_request1 = create_group.CreateGroupRequest(
        group_name="Group 1",
        group_description="First group",
        group_colour="#FF0000",
        friend_ids=[friend1.id],
    )
    create_request2 = create_group.CreateGroupRequest(
        group_name="Group 2",
        group_description="Second group",
        group_colour="#00FF00",
        friend_ids=[friend2.id],
    )

    with (
        patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"),
        patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
    ):
        response1 = await create_group.create_group(create_request1, auth, test_db)
        _ = await create_group.create_group(create_request2, auth, test_db)

    group1_id = response1["data"]

    # Fetch only group 1
    fetch_request = fetch_groups.FetchGroupsRequest(group_ids=[group1_id])
    response = await fetch_groups.fetch_all_groups(fetch_request, auth, test_db)

    assert response["success"] is True
    assert len(response["data"]) == 1
    assert response["data"][0]["group_name"] == "Group 1"


@pytest.mark.asyncio
async def test_fetch_groups_empty_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test fetch groups when user has no groups via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Fetch groups (should be empty)
    fetch_request = fetch_groups.FetchGroupsRequest(group_ids=None)
    response = await fetch_groups.fetch_all_groups(fetch_request, auth, test_db)

    assert response["success"] is True
    assert "data" in response
    assert len(response["data"]) == 0


@pytest.mark.asyncio
async def test_fetch_multiple_groups_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test fetching multiple groups via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    assert test_user.id is not None

    friend = await add_user("friend", 1004, test_db)
    assert friend.id is not None
    _, friend_token = await add_token(1000, 1000, test_db, friend.id)

    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    friend_auth: Tuple[User, UserToken] = (friend, friend_token)

    # Add and accept friend
    add_request = add_friend.AddFriendRequest(user_id=friend.id)
    with patch("src.util.rest_util.sio.emit", new_callable=AsyncMock):
        await add_friend.add_friend(add_request, auth, test_db)

    respond_request = respond_friend_request.RespondFriendRequest(
        friend_id=test_user.id, accept=True
    )
    with patch(
        "src.api.api_v1.friends.respond_friend_request.sio.emit", new_callable=AsyncMock
    ):
        await respond_friend_request.respond_friend_request(
            respond_request, friend_auth, test_db
        )

    # Create multiple groups
    for i in range(3):
        create_request = create_group.CreateGroupRequest(
            group_name=f"Group {i + 1}",
            group_description=f"Description {i + 1}",
            group_colour=f"#{i}{i}{i}{i}{i}{i}",
            friend_ids=[friend.id],
        )
        with (
            patch(
                "age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay"
            ),
            patch("src.util.rest_util.sio.emit", new_callable=AsyncMock),
        ):
            await create_group.create_group(create_request, auth, test_db)

    # Fetch all groups
    fetch_request = fetch_groups.FetchGroupsRequest(group_ids=None)
    response = await fetch_groups.fetch_all_groups(fetch_request, auth, test_db)

    assert response["success"] is True
    assert len(response["data"]) == 3
