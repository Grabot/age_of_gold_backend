from flask_socketio import Namespace
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit
from flask import request
from app import socks
from app.models.hexagon import Hexagon
from app.util.global_vars import map_size


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
        print("joined room: %s" % room)
        join_room(room)
        emit("message_event", 'User has entered room %s' % room, room=room, namespace='/api/v1.0/sock')

    # noinspection PyMethodMayBeStatic
    def on_leave(self, data):
        user_id = data["userId"]
        room = "room_%s" % user_id
        leave_room(room)
        print("left room %s" % room)
        emit("message_event", 'User has left room %s' % room, room=request.sid)

    # noinspection PyMethodMayBeStatic
    def on_get_hexagon(self, data):
        q = data["q"]
        r = data["r"]
        s = (q + r) * -1
        if q is not None and r is not None and s is not None:
            # If the hex is out of the map bounds we want it to loop around
            if q < -map_size or q > map_size or r < -map_size or r > map_size:
                wrap_q = 0
                while q > map_size:
                    q = q - (2 * map_size + 1)
                    wrap_q += 1
                while q < -map_size:
                    q = q + (2 * map_size + 1)
                    wrap_q -= 1
                wrap_r = 0
                while r > map_size:
                    r = r - (2 * map_size + 1)
                    wrap_r += 1
                while r < -map_size:
                    r = r + (2 * map_size + 1)
                    wrap_r -= 1

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


socks.on_namespace(NamespaceSock('/api/v1.0/sock'))

