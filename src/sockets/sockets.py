from typing import Any, Dict, Optional, Union, cast

import socketio
from redis import asyncio as aioredis
from redis.asyncio import Redis
from sqlmodel import select

from src.config.config import settings
from src.database import async_session
from src.models.chat import Chat
from src.models.message import Message
from src.models.user import User
from src.util.gold_logging import logger
from src.util.util import get_group_room, get_user_room

mgr = socketio.AsyncRedisManager(settings.REDIS_URI)
sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=mgr,
    cors_allowed_origins=settings.ALLOWED_ORIGINS_LIST,
)
sio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/socket.io")

redis: Redis = aioredis.from_url(settings.REDIS_URI)  # type: ignore[no-untyped-call]


@sio.on("connect")
async def handle_connect(sid: str, *args: Any, **kwargs: Any) -> None:
    print(f"Received connect: {sid}")


@sio.on("disconnect")
async def handle_disconnect(sid: str, *args: Any, **kwargs: Any) -> None:
    print(f"Received disconnect: {sid}")


@sio.on("message_event")
async def handle_message_event(sid: str, *args: Any, **kwargs: Any) -> None:
    print(f"Received message_event: {sid}")


@sio.on("join")
async def handle_join(sid: str, *args: Any, **kwargs: Any) -> None:
    print("join regular")
    data: Dict[str, Union[int, str]] = args[0]
    user_id: int = cast(int, data["user_id"])
    room: str = get_user_room(user_id)
    await sio.enter_room(sid, room)
    await sio.emit(
        "message_event",
        f"User has entered room {room}",
        room=room,
    )

    # Example of database calls with sockets
    async with async_session() as session:
        async with session.begin():
            user: Optional[User] = await session.get(User, user_id)
            if user:
                pass
            pass


@sio.on("join_group")
async def handle_join_group(sid: str, *args: Any, **kwargs: Any) -> None:
    print("Received join_group")
    data: Dict[str, Union[int, str]] = args[0]
    chat_id: int = cast(int, data["chat_id"])
    group_room: str = get_group_room(chat_id)
    print(f"room: {group_room}")
    await sio.enter_room(sid, group_room)
    await sio.emit(
        "message_event",
        f"User has entered group room {group_room}",
        room=group_room,
    )


@sio.on("leave")
async def handle_leave(sid: str, *args: Any, **kwargs: Any) -> None:
    print("leave regular")
    data: Dict[str, Union[int, str]] = args[0]
    user_id: int = cast(int, data["user_id"])
    room: str = get_user_room(user_id)
    await sio.leave_room(sid, room)
    await sio.emit(
        "message_event",
        f"User has left room {room}",
        room=sid,
    )


@sio.on("leave_group")
async def handle_leave_group(sid: str, *args: Any, **kwargs: Any) -> None:
    print("leave group")
    data: Dict[str, Union[int, str]] = args[0]
    chat_id: int = cast(int, data["chat_id"])
    group_room: str = get_group_room(chat_id)
    print(f"room: {group_room}")
    await sio.leave_room(sid, group_room)
    await sio.emit(
        "message_event",
        f"User has left group room {group_room}",
        room=sid,
    )

