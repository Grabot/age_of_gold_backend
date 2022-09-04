from flask_socketio import Namespace
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit
from flask import request
from app import socks
from app.models.hexagon import Hexagon
from app.util.global_vars import map_size
from app.util.util import get_wraparounds


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
        q = data["q"]
        r = data["r"]
        [q, _, r, _] = get_wraparounds(q, r)
        room = "%s_%s" % (q, r)
        join_room(room)
        print("joined hex room: %s" % room)
        emit("message_event", 'User is looking at hex %s %s and has entered room %s' % (q, r, room), room=room)

    # noinspection PyMethodMayBeStatic
    def on_leave_hex(self, data):
        q = data["q"]
        r = data["r"]
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
    def on_get_hexagon(self, data):
        q = data["q"]
        r = data["r"]
        s = (q + r) * -1
        if q is not None and r is not None and s is not None:
            # If the hex is out of the map bounds we want it to loop around
            if q < -map_size or q > map_size or r < -map_size or r > map_size:
                [q, wrap_q, r, wrap_r] = get_wraparounds(q, r)

                s = (q + r) * -1
                print("wraparound test! q: {} r: {} s: {}   wrap_q: {}  wrap_r: {}".format(q, r, s, wrap_q, wrap_q))
                hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
                # We will add a wraparound indicator
                return_hexagon = hexagon.serialize
                return_hexagon["wraparound"] = {
                    "q": wrap_q,
                    "r": wrap_r
                }
                emit("send_hexagon_success", return_hexagon, room=request.sid)
                return
            else:
                # The hex is within the map bounds so retrieve it
                hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
                if hexagon is None:
                    emit("send_hexagon_fail", 'hexagon getting failed', room=request.sid)
                else:
                    emit("send_hexagon_success", hexagon.serialize, room=request.sid)
        else:
            emit("send_hexagon_fail", 'hexagon getting failed', room=request.sid)

    # noinspection PyMethodMayBeStatic
    def on_send_message(self, data):
        user_name = data["user_name"]
        message = data["message"]
        print("we are going to send a message {} from user {}".format(message, user_name))
        print("we are going to send a message {} from user {}".format(message, user_name))
        emit("send_message_success", data, broadcast=True)


socks.on_namespace(NamespaceSock('/api/v1.0/sock'))

