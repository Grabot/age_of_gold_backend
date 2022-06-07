from flask import request
from flask_restful import Api
from flask_restful import Resource

from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db


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


def go_right(q, r, s, center_offset):
    # q = 9
    # r = -4
    # s = -5
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    q_for_tiles = 9 * center_offset
    r_for_tiles = -4 * center_offset
    s_for_tiles = -5 * center_offset
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    print("went right")


def go_left(q, r, s, center_offset):
    # q = -9
    # r = 4
    # s = 5
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    q_for_tiles = -9 * center_offset
    r_for_tiles = 4 * center_offset
    s_for_tiles = 5 * center_offset
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    print("went left")


def go_right_up(q, r, s, center_offset):
    # q = 4
    # r = 5
    # s = -9
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    q_for_tiles = 4 * center_offset
    r_for_tiles = 5 * center_offset
    s_for_tiles = -9 * center_offset
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    print("went right up?")
    return [q_for_tiles, r_for_tiles, s_for_tiles]


def go_left_up(q, r, s, center_offset):
    # q = -5
    # r = 9
    # s = -4
    hexagon = Hexagon(q=q, r=r, s=s)
    db.session.add(hexagon)
    db.session.commit()
    q_for_tiles = -5 * center_offset
    r_for_tiles = 9 * center_offset
    s_for_tiles = -4 * center_offset
    tiles = get_tiles(hexagon.id, q_for_tiles, r_for_tiles, s_for_tiles)
    for tile in tiles:
        db.session.add(tile)
    db.session.commit()
    print("went left up?")
    return [q_for_tiles, r_for_tiles, s_for_tiles]


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
        hexagon = Hexagon.query.filter_by(q=0, r=0, s=0).first()

        if hexagon is None:
            # for x in range(1, 5):
            #     q = x
            #     r = 0
            #     s = -x
            #     go_right(q, r, s, x)
            #     print("make hexagon %s of 5" % x)
            # for x in range(1, 5):
            #     q = -x
            #     r = 0
            #     s = x
            #     go_left(q, r, s, x)
            #     print("make hexagon %s of 5" % x)
            # for x in range(-3, 3):
            #     q = x
            #     r = -x
            #     s = 0
            #     go_right_up(q, r, s, x)
            # for x in range(-3, 3):
            #     q = 0
            #     r = -x
            #     s = x
            #     go_left_up(q, r, s, x)
            #     print("make hexagon %s" % x)
            hexagon = Hexagon(q=0, r=0, s=0)
            db.session.add(hexagon)
            db.session.commit()
            tiles = get_tiles(hexagon.id, 0, 0, 0)
            for tile in tiles:
                db.session.add(tile)
            go_right_up(1, -1, 0, 1)
            go_left_up(1, -2, 1, 0)

        else:
            return {
                "result": True,
                "message": "map already created"
            }


api = Api(app_api)
api.add_resource(MapRest, '/api/v1.0/map', endpoint='map')
