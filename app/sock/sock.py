from flask_socketio import Namespace
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit
from flask import request
from app import socks
from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.models.user import User
from app.util.util import get_wraparounds
from app import db
from app.config import DevelopmentConfig
import json


class NamespaceSock(Namespace):

    # noinspection PyMethodMayBeStatic
    def on_connect(self):
        print("on_connect")
        pass

    # noinspection PyMethodMayBeStatic
    def on_disconnect(self):
        print("on_disconnect")
        pass

    # noinspection PyMethodMayBeStatic
    def on_message_event(self, data):
        print("on_message_event")
        pass

    # noinspection PyMethodMayBeStatic
    def on_join(self, data):
        user_id = data["userId"]
        room = "room_%s" % user_id
        # print("joined room: %s" % room)
        join_room(room)
        emit("message_event", 'User has entered room %s' % room, room=room, namespace='/api/v1.0/sock')

    # noinspection PyMethodMayBeStatic
    def on_join_hex(self, data):
        map_size = DevelopmentConfig.map_size
        q = data["q"]
        r = data["r"]
        if q < -map_size or q > map_size or r < -map_size or r > map_size:
            [q, _, r, _] = get_wraparounds(q, r)
        room = "%s_%s" % (q, r)
        join_room(room)
        # print("joined hex room: %s" % room)
        emit("message_event", 'User is looking at hex %s %s and has entered room %s' % (q, r, room), room=room)

    # noinspection PyMethodMayBeStatic
    def on_leave_hex(self, data):
        map_size = DevelopmentConfig.map_size
        q = data["q"]
        r = data["r"]
        if q < -map_size or q > map_size or r < -map_size or r > map_size:
            [q, _, r, _] = get_wraparounds(q, r)
        room = "%s_%s" % (q, r)
        leave_room(room)
        # print("left hex room: %s" % room)
        emit("message_event", 'User has left hex room %s' % room, room=request.sid)

    # noinspection PyMethodMayBeStatic
    def on_leave(self, data):
        user_id = data["userId"]
        room = "room_%s" % user_id
        leave_room(room)
        # print("left room %s" % room)
        emit("message_event", 'User has left room %s' % room, room=request.sid)

    # noinspection PyMethodMayBeStatic
    def on_send_message(self, data):
        emit("send_message_success", data, broadcast=True)


socks.on_namespace(NamespaceSock(DevelopmentConfig.API_SOCK_NAMESPACE))

