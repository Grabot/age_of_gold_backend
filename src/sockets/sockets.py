from typing import Any, Dict, Optional, Union, cast

import socketio

from src.config.config import settings
from src.database import async_session
from src.models.user import User
from redis import asyncio as aioredis

mgr = socketio.AsyncRedisManager(settings.REDIS_URI)
sio = socketio.AsyncServer(
    async_mode="asgi", client_manager=mgr, cors_allowed_origins="*"
)
sio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/socket.io")

redis = aioredis.from_url(settings.REDIS_URI)


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
    data: Dict[str, Union[int, str]] = args[0]
    user_id: int = cast(int, data["user_id"])
    room: str = f"room_{user_id}"
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


@sio.on("leave")
async def handle_leave(sid: str, *args: Any, **kwargs: Any) -> None:
    data: Dict[str, Union[int, str]] = args[0]
    user_id: int = cast(int, data["user_id"])
    room: str = f"room_{user_id}"
    await sio.leave_room(sid, room)
    await sio.emit(
        "message_event",
        f"User has left room {room}",
        room=sid,
    )
