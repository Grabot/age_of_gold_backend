from flask import request
from flask_restful import Api
from flask_restful import Resource

from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db
from app.util import global_vars
import json


radius = 4
# a hex section with radius r is Cube(2 * r+1, -r, -r-1)
# with 6 rotations
# [q, r, s]
# [-r, -s, -q]
# [s, q, r]
# [-s, -q, -r]
# [r, s, q]
# [-q, -r, -s]
# So if the center hex is 0, 0, 0
# on of the side hexagons with the radius of 4 would be 9, -4, -5


def create_tile(hexagon_id, _q, _r, _s):
    combined = _q + _r + _s
    if combined != 0:
        print("BIG ERROR!!!!")
        print("q: %s, r: %s, s: %s" % (_q, _r, _s))
        exit()
    return Tile(q=_q, r=_r, s=_s, hexagon_id=hexagon_id, type=0)


def get_tiles(hexagon_id, q, r, s):
    # For now, we will define each of the tiles in the hexagon separate
    tiles = []
    tiles.append(create_tile(hexagon_id, q - 4, r + 0, s + 4))
    tiles.append(create_tile(hexagon_id, q - 3, r - 1, s + 4))
    tiles.append(create_tile(hexagon_id, q - 2, r - 2, s + 4))
    tiles.append(create_tile(hexagon_id, q - 1, r - 3, s + 4))
    tiles.append(create_tile(hexagon_id, q + 0, r - 4, s + 4))
    tiles.append(create_tile(hexagon_id, q - 4, r + 1, s + 3))
    tiles.append(create_tile(hexagon_id, q - 3, r + 0, s + 3))
    tiles.append(create_tile(hexagon_id, q - 2, r - 1, s + 3))
    tiles.append(create_tile(hexagon_id, q - 1, r - 2, s + 3))
    tiles.append(create_tile(hexagon_id, q + 0, r - 3, s + 3))
    tiles.append(create_tile(hexagon_id, q + 1, r - 4, s + 3))
    tiles.append(create_tile(hexagon_id, q - 4, r + 2, s + 2))
    tiles.append(create_tile(hexagon_id, q - 3, r + 1, s + 2))
    tiles.append(create_tile(hexagon_id, q - 2, r + 0, s + 2))
    tiles.append(create_tile(hexagon_id, q - 1, r - 1, s + 2))
    tiles.append(create_tile(hexagon_id, q + 0, r - 2, s + 2))
    tiles.append(create_tile(hexagon_id, q + 1, r - 3, s + 2))
    tiles.append(create_tile(hexagon_id, q + 2, r - 4, s + 2))
    tiles.append(create_tile(hexagon_id, q - 4, r + 3, s + 1))
    tiles.append(create_tile(hexagon_id, q - 3, r + 2, s + 1))
    tiles.append(create_tile(hexagon_id, q - 2, r + 1, s + 1))
    tiles.append(create_tile(hexagon_id, q - 1, r + 0, s + 1))
    tiles.append(create_tile(hexagon_id, q + 0, r - 1, s + 1))
    tiles.append(create_tile(hexagon_id, q + 1, r - 2, s + 1))
    tiles.append(create_tile(hexagon_id, q + 2, r - 3, s + 1))
    tiles.append(create_tile(hexagon_id, q + 3, r - 4, s + 1))
    tiles.append(create_tile(hexagon_id, q - 4, r + 4, s + 0))
    tiles.append(create_tile(hexagon_id, q - 3, r + 3, s + 0))
    tiles.append(create_tile(hexagon_id, q - 2, r + 2, s + 0))
    tiles.append(create_tile(hexagon_id, q - 1, r + 1, s + 0))
    tiles.append(create_tile(hexagon_id, q - 0, r + 0, s + 0))
    tiles.append(create_tile(hexagon_id, q + 1, r - 1, s + 0))
    tiles.append(create_tile(hexagon_id, q + 2, r - 2, s + 0))
    tiles.append(create_tile(hexagon_id, q + 3, r - 3, s + 0))
    tiles.append(create_tile(hexagon_id, q + 4, r - 4, s + 0))
    tiles.append(create_tile(hexagon_id, q - 3, r + 4, s - 1))
    tiles.append(create_tile(hexagon_id, q - 2, r + 3, s - 1))
    tiles.append(create_tile(hexagon_id, q - 1, r + 2, s - 1))
    tiles.append(create_tile(hexagon_id, q + 0, r + 1, s - 1))
    tiles.append(create_tile(hexagon_id, q + 1, r + 0, s - 1))
    tiles.append(create_tile(hexagon_id, q + 2, r - 1, s - 1))
    tiles.append(create_tile(hexagon_id, q + 3, r - 2, s - 1))
    tiles.append(create_tile(hexagon_id, q + 4, r - 3, s - 1))
    tiles.append(create_tile(hexagon_id, q - 2, r + 4, s - 2))
    tiles.append(create_tile(hexagon_id, q - 1, r + 3, s - 2))
    tiles.append(create_tile(hexagon_id, q + 0, r + 2, s - 2))
    tiles.append(create_tile(hexagon_id, q + 1, r + 1, s - 2))
    tiles.append(create_tile(hexagon_id, q + 2, r + 0, s - 2))
    tiles.append(create_tile(hexagon_id, q + 3, r - 1, s - 2))
    tiles.append(create_tile(hexagon_id, q + 4, r - 2, s - 2))
    tiles.append(create_tile(hexagon_id, q - 1, r + 4, s - 3))
    tiles.append(create_tile(hexagon_id, q + 0, r + 3, s - 3))
    tiles.append(create_tile(hexagon_id, q + 1, r + 2, s - 3))
    tiles.append(create_tile(hexagon_id, q + 2, r + 1, s - 3))
    tiles.append(create_tile(hexagon_id, q + 3, r + 0, s - 3))
    tiles.append(create_tile(hexagon_id, q + 4, r - 1, s - 3))
    tiles.append(create_tile(hexagon_id, q + 0, r + 4, s - 4))
    tiles.append(create_tile(hexagon_id, q + 1, r + 3, s - 4))
    tiles.append(create_tile(hexagon_id, q + 2, r + 2, s - 4))
    tiles.append(create_tile(hexagon_id, q + 3, r + 1, s - 4))
    tiles.append(create_tile(hexagon_id, q + 4, r + 0, s - 4))
    return tiles


def go_right(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles):
    # q = 9
    # r = -4
    # s = -5
    # Go right so q += 1 and s -= 1
    index = 0
    while index < global_vars.map_size:
        q += 1
        s -= 1
        hexagon = Hexagon(q=q, r=r, s=s)
        db.session.add(hexagon)
        db.session.commit()
        print("created hexagon (right) with q: %s r: %s s: %s and id: %s" % (q, r, s, hexagon.id))
        q_for_tiles += 9
        r_for_tiles -= 4
        s_for_tiles -= 5
        tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
        for tile in tiles:
            db.session.add(tile)
        db.session.commit()
        index += 1
    return [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles]


def go_left(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles):
    # q = -9
    # r = 4
    # s = 5
    # Go left so q -= 1 and s += 1
    index = 0
    while index < global_vars.map_size:
        q -= 1
        s += 1
        hexagon = Hexagon(q=q, r=r, s=s)
        db.session.add(hexagon)
        db.session.commit()
        print("created hexagon (left) with q: %s r: %s s: %s and id: %s" % (q, r, s, hexagon.id))
        q_for_tiles -= 9
        r_for_tiles += 4
        s_for_tiles += 5
        tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
        for tile in tiles:
            db.session.add(tile)
        db.session.commit()
        index += 1
    return [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles]


def go_right_up(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles):
    # q = 4
    # r = 5
    # s = -9
    # Go right up so q += 1 and r -= 1
    q += 1
    r -= 1
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    print("created hexagon (right up) with q: %s r: %s s: %s and id: %s" % (q, r, s, hexagon.id))
    q_for_tiles += 4
    r_for_tiles += 5
    s_for_tiles -= 9
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    return [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles]


def go_left_up(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles):
    # q = -5
    # r = 9
    # s = -4
    # go left up, so q += 0 r -= 1 and s += 1
    r -= 1
    s += 1
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    print("created hexagon (left up) with q: %s r: %s s: %s and id: %s" % (q, r, s, hexagon.id))
    q_for_tiles -= 5
    r_for_tiles += 9
    s_for_tiles -= 4
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    return [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles]


def go_left_down(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles):
    # q = -4
    # r = -5
    # s = 9
    # Go left down so q -= 1 and r += 1
    q -= 1
    r += 1
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    print("created hexagon (left down) with q: %s r: %s s: %s and id: %s" % (q, r, s, hexagon.id))
    q_for_tiles -= 4
    r_for_tiles -= 5
    s_for_tiles += 9
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    return [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles]


def go_right_down(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles):
    # q = 5
    # r = -9
    # s = 4
    # Go right down so r += 1 and s -= 1
    r += 1
    s -= 1
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    print("created hexagon (right down) with q: %s r: %s s: %s and id: %s" % (q, r, s, hexagon.id))
    q_for_tiles += 5
    r_for_tiles -= 9
    s_for_tiles += 4
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    return [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles]


class MapRest(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        return {"Hello": "Map"}

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        json_data = request.get_json(force=True)
        print("post map: %s" % json_data)
        hexagon = Hexagon.query.filter_by(q=0, r=0, s=0).first()

        if hexagon is None:
            # map_size = global_vars.map_size
            q = 0
            r = 0
            s = 0
            q_for_tiles = 0
            r_for_tiles = 0
            s_for_tiles = 0
            # center tile with left and right hexagons
            hexagon = Hexagon(q=q, r=r, s=s)
            db.session.add(hexagon)
            db.session.commit()
            tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
            for tile in tiles:
                db.session.add(tile)
            db.session.commit()
            [_, _, _, _, _, _] = go_left(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)
            [_, _, _, _, _, _] = go_right(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)

            # going up
            for x in range(0, global_vars.map_size):
                [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles] \
                    = go_left_up(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)
                [_, _, _, _, _, _] = go_left(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)
                [_, _, _, _, _, _] = go_right(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)

            # going down, we reset back to the center for this.
            q = 0
            r = 0
            s = 0
            q_for_tiles = 0
            r_for_tiles = 0
            s_for_tiles = 0
            for x in range(0, global_vars.map_size):
                [q, r, s, q_for_tiles, r_for_tiles, s_for_tiles] \
                    = go_right_down(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)
                [_, _, _, _, _, _] = go_left(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)
                [_, _, _, _, _, _] = go_right(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)

        else:
            return {
                "result": True,
                "message": "map already created"
            }


api = Api(app_api)
api.add_resource(MapRest, '/api/v1.0/map', endpoint='map')
