from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
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

    statement = select(Friend).where(
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


async def get_user_from_db(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user from the database using a select statement.

    Returns the User object if found, None otherwise.
    """
    user_statement = select(User).where(User.id == user_id)
    results_user = await db.execute(user_statement)
    result_user = results_user.first()
    if result_user is None:
        return None

    return result_user.User


async def update_friend_versions_and_notify(
    db: AsyncSession, user_id: int, event_name: str, event_data: dict
) -> None:
    """Update friend versions and notify friends about changes.

    This function finds all friends of a user, increments their friend_version,
    and sends a socket notification to each friend.

    Args:
        db: Database session
        user_id: ID of the user whose friends need updating
        event_name: Name of the socket event to emit
        event_data: Data to send with the socket event
    """

    friends_statement = select(Friend).where(Friend.friend_id == user_id)
    friends_result = await db.execute(friends_statement)
    friends = friends_result.scalars().all()

    for friend in friends:
        friend.friend_version += 1
        db.add(friend)
        friend_room = get_user_room(friend.user_id)
        await sio.emit(event_name, event_data, room=friend_room)
