from typing import Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import or_, select

from src.models import Friend, User
from src.sockets.sockets import sio
from src.util.util import get_user_room


async def get_friend_request_pair(
    db: AsyncSession, me_id: int, friend_id: int
) -> Tuple[Friend, Friend]:
    """Get both friend request entries for a friendship.

    Returns the friend request from the current user's perspective and the reciprocal.
    Raises HTTPException if the friendship is not properly set up.
    """
    from fastapi import HTTPException

    statement: Select = select(Friend).where(
        or_(
            (Friend.user_id == me_id) & (Friend.friend_id == friend_id),
            (Friend.user_id == friend_id) & (Friend.friend_id == me_id),
        )
    )
    result = await db.execute(statement)
    friends = result.scalars().all()

    friend_request: Friend | None = next(
        (f for f in friends if f.user_id == me_id), None
    )
    reciprocal_friend: Friend | None = next(
        (f for f in friends if f.user_id == friend_id), None
    )

    if len(friends) != 2 or friend_request is None or reciprocal_friend is None:
        raise HTTPException(
            status_code=404,
            detail="Friend request not found",
        )

    return friend_request, reciprocal_friend


async def get_user_from_db(db: AsyncSession, user_id: int) -> User | None:
    """Get a user from the database by ID."""
    return await db.get(User, user_id)


async def update_friend_versions_and_notify(
    db: AsyncSession, user_id: int, event_name: str, event_data: dict[str, Any]
) -> None:
    """Update friend versions and notify friends about changes.

    This function finds all friends of a user, increments their friend_version,
    and sends a socket notification to each friend.
    """

    friends_statement: Select = select(Friend).where(Friend.friend_id == user_id)
    friends_result = await db.execute(friends_statement)
    friends = friends_result.scalars().all()

    for friend in friends:
        friend.friend_version += 1
        db.add(friend)
        friend_room = get_user_room(friend.user_id)
        await sio.emit(event_name, event_data, room=friend_room)
