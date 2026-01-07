"""Test file for the friend model."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Friend, User


@pytest.mark.asyncio
async def test_friend_user_connection(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test that a Friend is correctly created and linked to user"""
    user = User(
        id=10,
        username="user",
        email_hash="email_hash",
        password_hash="password_hash",
        salt="salt",
        origin=0,
        default_avatar=True,
        profile_version=0,
        avatar_version=0,
    )
    user_friend = User(
        id=11,
        username="user_friend",
        email_hash="email_hash",
        password_hash="password_hash",
        salt="salt",
        origin=0,
        default_avatar=True,
        profile_version=0,
        avatar_version=0,
    )
    test_db.add(user)
    test_db.add(user_friend)
    await test_db.commit()
    await test_db.refresh(user_friend)
    await test_db.refresh(user)
    friend_1 = Friend(
        id=10,
        user_id=10,
        friend_id=11,
        accepted=True,
        friend_version=4,
    )
    friend_2 = Friend(
        id=11,
        user_id=11,
        friend_id=10,
        accepted=True,
        friend_version=7,
    )
    test_db.add(friend_1)
    test_db.add(friend_2)
    await test_db.commit()
    await test_db.refresh(friend_1)
    await test_db.refresh(friend_2)

    assert friend_1.friend is not None
    assert friend_1.friend is user_friend
    assert friend_2.friend is not None
    assert friend_2.friend is user


def test_friend_serialize() -> None:
    """Test that the serialize property returns a dictionary with the correct friend data"""
    friend = Friend(
        id=101,
        user_id=101,
        friend_id=121,
        accepted=True,
        friend_version=4,
    )
    friend_user = friend.serialize
    assert isinstance(friend_user, dict)
    assert friend_user["id"] == 101
    assert friend_user["data"]["user_id"] == 101
    assert friend_user["data"]["friend_id"] == 121
    assert friend_user["data"]["accepted"]
