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
        emit("message_event", 'User has entered room %s' % room, room=room)

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
        user_id = data["userId"]
        room = "room_%s" % user_id
        if q is not None and r is not None and s is not None:
            # q is on the other side, but r is still good.
            if q > map_size and (-4 <= r <= 4):
                wrap_q = 0
                while q > map_size:
                    q = q - (2 * map_size + 1)
                    wrap_q += 1
                s = (q + r) * -1
                print("wraparound test! q: {} r: {} s: {}   wrap_q: {}".format(q, r, s, wrap_q))
                hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
                # We will add a wraparound indicator
                return_hexagon = hexagon.serialize
                return_hexagon["wraparound"] = {
                    "q": wrap_q,
                    "r": 0
                }
                emit("send_hexagon_success", return_hexagon, room=room)
                return
            elif (-4 <= q <= 4) and r > map_size:
                wrap_r = 0
                while r > map_size:
                    r = r - (2 * map_size + 1)
                    wrap_r += 1
                s = (q + r) * -1
                print("wraparound test 2! q: {} r: {} s: {}   wrap r: {}".format(q, r, s, wrap_r))
                hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
                return_hexagon = hexagon.serialize
                return_hexagon["wraparound"] = {
                    "q": 0,
                    "r": wrap_r
                }
                emit("send_hexagon_success", return_hexagon, room=room)
                return
            elif q > map_size and r > map_size:
                wrap_q = 0
                while q > map_size:
                    q = q - (2 * map_size + 1)
                    wrap_q += 1
                wrap_r = 0
                while r > map_size:
                    r = r - (2 * map_size + 1)
                    wrap_r += 1
                s = (q + r) * -1
                print("wraparound test 3! q: {} r: {} s: {}  wrap_q: {}   wrap_r: {}".format(q, r, s, wrap_q, wrap_r))
                hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
                return_hexagon = hexagon.serialize
                return_hexagon["wraparound"] = {
                    "q": wrap_q,
                    "r": wrap_r
                }
                emit("send_hexagon_success", return_hexagon, room=room)
                return
            else:
                hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
            if hexagon is None:
                emit("send_hexagon_fail", 'hexagon getting failed', room=room)
            else:
                emit("send_hexagon_success", hexagon.serialize, room=room)
        else:
            emit("send_hexagon_fail", 'hexagon getting failed', room=room)

    # noinspection PyMethodMayBeStatic
    def on_get_hexagons_q(self, data):
        q_begin = data["q_begin"]
        q_end = data["q_end"]
        r_row = data["r_row"]
        user_id = data["userId"]
        room = "room_%s" % user_id
        if q_begin is not None and q_end is not None and r_row is not None:
            hexagons = Hexagon.query.filter(Hexagon.q.between(q_begin, q_end)).filter(Hexagon.r == r_row).all()
            return_hexagons = []
            for hexagon in hexagons:
                return_hexagons.append(hexagon.serialize)
            emit("send_hexagons_success", return_hexagons, room=room)

    # noinspection PyMethodMayBeStatic
    def on_get_hexagons_r(self, data):
        r_begin = data["r_begin"]
        r_end = data["r_end"]
        q_row = data["q_row"]
        user_id = data["userId"]
        room = "room_%s" % user_id
        if r_begin is not None and r_end is not None and q_row is not None:
            hexagons = Hexagon.query.filter(Hexagon.r.between(r_begin, r_end)).filter(Hexagon.q == q_row).all()
            return_hexagons = []
            for hexagon in hexagons:
                return_hexagons.append(hexagon.serialize)
            emit("send_hexagons_success", return_hexagons, room=room)

    # # noinspection PyMethodMayBeStatic
    # def on_message(self, data):
    #     send_message(data)


socks.on_namespace(NamespaceSock('/api/v1.0/sock'))

