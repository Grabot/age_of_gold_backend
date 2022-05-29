from flask_socketio import Namespace
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit
from flask import request
from app import socks
from app.models.hexagon import Hexagon


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
        print("joined: %s" % user_id)
        join_room(user_id)
        emit("message_event", 'User has entered room %s' % user_id, room=user_id)

    # noinspection PyMethodMayBeStatic
    def on_get_hexagon(self, data):
        print("trying to get a hexagon")
        q = data["q"]
        r = data["r"]
        s = data["s"]
        user_id = data["userId"]
        print("hexagon %s %s %s with user %s" % (q, r, s, user_id))
        if q is not None and r is not None and s is not None:
            hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
            if hexagon is None:
                emit("send_hexagon_fail", 'hexagon getting failed', room=user_id)
            else:
                emit("send_hexagon_success", hexagon.serialize, room=user_id)
        else:
            emit("send_hexagon_fail", 'hexagon getting failed', room=user_id)

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

