from flask import request
from flask_restful import Api
from flask_restful import Resource

from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db
from app.util import global_vars


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
    index = -global_vars.map_size - 1
    while index < global_vars.map_size:
        hexagon = Hexagon(q=q, r=r, s=s)
        db.session.add(hexagon)
        db.session.commit()
        print("created hexagon (right) with q: %s r: %s s: %s and id: %s" % (q, r, s, hexagon.id))

        tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
        for tile in tiles:
            db.session.add(tile)
        db.session.commit()
        q += 1
        s -= 1
        q_for_tiles += 9
        r_for_tiles -= 4
        s_for_tiles -= 5
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


class MapRest(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        print("get map")
        return {"Hello": "Map"}

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        json_data = request.get_json(force=True)
        print("post map: %s" % json_data)
        r = json_data["r"]
        if r is None:
            return {"result": "please provide a row"}
        hexagon = Hexagon.query.filter_by(q=0, r=r).first()

        if hexagon is None:
            # map_size = global_vars.map_size
            # We go from the leftmost place all the way to the right.
            q = -global_vars.map_size
            s = (q + r) * -1
            # First adapt it to the row
            q_for_tiles = (5 * r)
            r_for_tiles = (-9 * r)
            # Then adapt it to the column
            q_for_tiles += (9 * q)
            r_for_tiles += (-4 * q)
            s_for_tiles = (q_for_tiles + r_for_tiles) * -1

            [_, _, _, _, _, _] = go_right(q, r, s, q_for_tiles, r_for_tiles, s_for_tiles)
            return {
                "result": True,
                "message": "Row %s successfully created!" % r
            }
        else:
            return {
                "result": True,
                "message": "Row already created"
            }


api = Api(app_api)
api.add_resource(MapRest, '/api/v1.0/map/row', endpoint='map_row')
