import socketio

from app.config.config import settings
from app.util.util import get_wraparounds

mgr = socketio.AsyncRedisManager(settings.REDIS_URI)
sio = socketio.AsyncServer(async_mode="asgi", client_manager=mgr, cors_allowed_origins="*")
sio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/socket.io")


@sio.on("connect")
async def handle_connect(sid, *args, **kwargs):
    print(f"Received connect: {sid}")
    # await sio.emit('lobby', 'User joined')


@sio.on("disconnect")
async def handle_disconnect(sid, *args, **kwargs):
    print(f"Received disconnect: {sid}")
    # await sio.emit('lobby', 'User joined')


@sio.on("message_event")
async def handle_message_event(sid, *args, **kwargs):
    print(f"Received message_event: {sid}")


@sio.on("join")
async def handle_join(sid, *args, **kwargs):
    data = args[0]
    user_id = data["user_id"]
    if user_id != -1:
        room = "room_%s" % user_id
        print("joined room: %s" % room)
        sio.enter_room(sid, room)
        await sio.emit(
            "message_event",
            "User has entered room %s" % room,
            room=room,
        )


@sio.on("join_guild")
async def handle_join_guild(sid, *args, **kwargs):
    data = args[0]
    guild_id = data["guild_id"]
    if guild_id != -1:
        room = "guild_%s" % guild_id
        sio.enter_room(sid, room)
        await sio.emit(
            "message_event",
            "Guild member has entered their guild room %s" % room,
            room=room,
        )


@sio.on("leave")
async def handle_leave(sid, *args, **kwargs):
    data = args[0]
    user_id = data["userId"]
    if user_id != -1:
        room = "room_%s" % user_id
        sio.leave_room(sid, room)
        print("left room %s" % room)
        await sio.emit(
            "message_event",
            "User has left room %s" % room,
            room=sid,
        )


@sio.on("join_hex")
async def handle_join_hex(sid, *args, **kwargs):
    data = args[0]
    map_size = settings.map_size
    q = data["q"]
    r = data["r"]
    if q < -map_size or q > map_size or r < -map_size or r > map_size:
        [q, _, r, _] = get_wraparounds(q, r)
    room = "%s_%s" % (q, r)
    sio.enter_room(sid, room)
    await sio.emit(
        "message_event",
        "User is looking at hex %s %s and has entered room %s" % (q, r, room),
        room=room,
    )
    print("joined hex room: %s" % room)


@sio.on("leave_hex")
async def handle_leave_hex(sid, *args, **kwargs):
    data = args[0]
    map_size = settings.map_size
    q = data["q"]
    r = data["r"]
    if q < -map_size or q > map_size or r < -map_size or r > map_size:
        [q, _, r, _] = get_wraparounds(q, r)
    room = "%s_%s" % (q, r)
    sio.leave_room(sid, room)
    await sio.emit(
        "message_event",
        "User has left hex room %s" % room,
        room=room,
    )
    print("left hex room: %s" % room)
