from flask_socketio import Namespace
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit
from flask import request
from app import socks


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
        print("joined")
        room = data["room"]
        join_room(room)
        emit("message_event", 'User has entered room %s' % room, room=room)

    # noinspection PyMethodMayBeStatic
    def on_join_solo(self, data):
        join_room(request.sid)
        emit("message_event", 'User has entered room %s' % request.sid, room=request.sid)

    # noinspection PyMethodMayBeStatic
    def on_leave(self, data):
        room = data["room"]
        leave_room(room)
        emit("message_event", 'User has left room %s' % room, room=request.sid)

    # noinspection PyMethodMayBeStatic
    def on_leave_solo(self, data):
        room = request.sid
        leave_room(room)
        emit("message_event", 'User has left room %s' % room, room=request.sid)

    # # noinspection PyMethodMayBeStatic
    # def on_message(self, data):
    #     send_message(data)


socks.on_namespace(NamespaceSock('/api/v1.0/sock'))

