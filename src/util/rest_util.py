from typing import Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import or_, select

from src.models import Friend, User, Chat
from src.sockets.sockets import sio
from src.util.util import get_group_room, get_user_room


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


async def update_group_versions_and_notify(
    chat: Chat,
    db: AsyncSession,
    event_name: str,
    event_data: dict[str, Any],
) -> None:
    """Update group versions and notify members about changes.

    Args:
        chat: The chat object containing groups
        db: Database session
        me: Current user who triggered the change
        event_name: Socket.io event name
        event_data: Data to send with the event
        exclude_sender: Whether to exclude the sender from notifications
    """
    # Update group versions
    for group in chat.groups:
        group.group_version += 1
        db.add(group)
    await db.commit()

    await sio.emit(event_name, event_data, room=get_group_room(chat.id))


async def emit_friend_response(
    event_name: str,
    user: User,
    recipient_room: str,
    additional_data: dict[str, Any] | None = None,
) -> None:
    """.

    Args:
        event_name: Name of the event to emit
        user: User object to create response data for
        recipient_room: Room ID of the recipient
        additional_data: Additional data to include in the response dictionary
    """
    response_data = {
        "friend_id": user.id,
        "username": user.username,
        "avatar_version": user.avatar_version,
        "profile_version": user.profile_version,
        "colour": user.colour,
    }

    if additional_data:
        response_data.update(additional_data)

    await sio.emit(
        event_name,
        response_data,
        room=recipient_room,
    )


async def emit_group_response(
    event_name: str,
    chat: Chat,
    recipient_room: str,
    additional_data: dict[str, Any] | None = None,
) -> None:
    response_data: dict[str, Any] = {
        "chat_id": chat.id,
        "name": chat.name,
        "description": chat.description,
        "colour": chat.colour,
    }

    if additional_data:
        response_data.update(additional_data)

    await sio.emit(
        event_name,
        response_data,
        room=recipient_room,
    )


async def update_user_field(
    db: AsyncSession,
    me: User,
    field_name: str,
    new_value: str,
    event_type: str,
) -> None:
    """Helper function to update a user field and notify friends."""
    me.profile_version += 1
    db.add(me)

    await update_friend_versions_and_notify(
        db,
        me.id,  # type: ignore
        event_type,
        {
            "user_id": me.id,
            field_name: new_value,
            "profile_version": me.profile_version,
        },
    )

    await db.commit()
