from flask_socketio import Namespace
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit
from flask import request
from app import socks
from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.util.global_vars import map_size
from app.util.util import get_wraparounds, cleanup
from app import db
import time
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
    def on_get_hexagon(self, data):
        start_time = time.time()
        q = data["q"]
        r = data["r"]
        print("%s_%s start with getting hexagons" % (q, r))
        # s = (q + r) * -1
        # If the hex is out of the map bounds we want it to loop around
        if q < -map_size or q > map_size or r < -map_size or r > map_size:
            [q, wrap_q, r, wrap_r] = get_wraparounds(q, r)

            # s = (q + r) * -1
            # print("wraparound test! q: {} r: {} s: {}   wrap_q: {}  wrap_r: {}".format(q, r, s, wrap_q, wrap_q))
            hexagon = Hexagon.query.filter_by(q=q, r=r).first()
            # cleanup(db.session)
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
            hexagon = Hexagon.query.filter_by(q=q, r=r).first()
            if hexagon is None:
                emit("send_hexagon_fail", 'hexagon getting failed', room=request.sid)
            else:
                # end_time = time.time()
                # total_time = end_time - start_time
                # print("%s_%s finished with getting BEFORE hexagons %s" % (q, r, total_time))
                return_thing = hexagon.serialize
                # end_time = time.time()
                # total_time = end_time - start_time
                # print("%s_%s finished with getting AFTER hexagons %s" % (q, r, total_time))
                emit("send_hexagon_success", return_thing, room=request.sid)

    # noinspection PyMethodMayBeStatic
    def on_send_message(self, data):
        emit("send_message_success", data, broadcast=True)

    # noinspection PyMethodMayBeStatic
    def on_change_tile_type(self, data):
        q = data["q"]
        r = data["r"]
        # s = (q + r) * -1
        tile_type = data["type"]
        tile = Tile.query.filter_by(q=q, r=r).first()
        if tile:
            tile.type = tile_type
            tile_hexagon = Hexagon.query.filter_by(id=tile.hexagon_id).first()
            if tile_hexagon:
                tiles = tile_hexagon.tiles
                tiles_info = []
                for tile in tiles:
                    tiles_info.append(tile.serialize)
                tile_hexagon.tiles_detail = json.dumps(tiles_info)
                db.session.add(tile)
                db.session.add(tile_hexagon)
                db.session.commit()
                return_hexagon = tile_hexagon.serialize
                return_hexagon["wraparound"] = {
                    "q": data["wrap_q"],
                    "r": data["wrap_r"]
                }
                room = "%s_%s" % (q, r)
                emit("send_hexagon_success", return_hexagon, room=room)
            else:
                emit("change_tile_type_failed", room=request.sid)
        else:
            emit("change_tile_type_failed", room=request.sid)


socks.on_namespace(NamespaceSock('/api/v1.0/sock'))

