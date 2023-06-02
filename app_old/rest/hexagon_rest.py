from flask import request
from flask_restful import Api, Resource

from app_old import db
from app_old.models.hexagon import Hexagon
from app_old.models.tile import Tile
from app_old.rest import app_api

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

# {
#     "q": 0,
#     "r": 0,
#     "s": 0
# }
# q = 0
# r = 0
# {
#     "q": 9,
#     "r": -4,
#     "s": -5
# }
# q = 1
# r = 0
# {
#     "q": 4,
#     "r": 5,
#     "s": -9
# }
# q = 1
# r = -1
# {
#     "q": -5,
#     "r": 9,
#     "s": -4
# }
# q = 0
# r = -1
# {
#     "q": 5,
#     "r": -9,
#     "s": 4
# }
# q = 0
# r = 1
# {
#     "q": -4,
#     "r": -5,
#     "s": 9
# }
# q = -1
# r = 1
# {
#     "q": -9,
#     "r": 4,
#     "s": 5
# }
# q = -1
# r = 0


def create_tile(hexagon_id, _q, _r):
    return Tile(q=_q, r=_r, hexagon_id=hexagon_id, type=0)


def get_tiles(hexagon_id, _q, _r):
    # For now, we will define each of the tiles in the hexagon separate
    tiles = []
    q = 0
    r = 0

    if _q == 0 and _r == 0:
        q = 0
        r = 0
    elif _q == 1 and _r == 0:
        q = 9
        r = -4
    elif _q == 1 and _r == -1:
        q = 4
        r = 5
    elif _q == 0 and _r == -1:
        q = -5
        r = 9
    elif _q == 0 and _r == 1:
        q = 5
        r = -9
    elif _q == -1 and _r == 1:
        q = -4
        r = -5
    elif _q == -1 and _r == 0:
        q = -9
        r = 4

    tiles.append(create_tile(hexagon_id, q - 4, r + 0))
    tiles.append(create_tile(hexagon_id, q - 3, r - 1))
    tiles.append(create_tile(hexagon_id, q - 2, r - 2))
    tiles.append(create_tile(hexagon_id, q - 1, r - 3))
    tiles.append(create_tile(hexagon_id, q + 0, r - 4))
    tiles.append(create_tile(hexagon_id, q - 4, r + 1))
    tiles.append(create_tile(hexagon_id, q - 3, r + 0))
    tiles.append(create_tile(hexagon_id, q - 2, r - 1))
    tiles.append(create_tile(hexagon_id, q - 1, r - 2))
    tiles.append(create_tile(hexagon_id, q + 0, r - 3))
    tiles.append(create_tile(hexagon_id, q + 1, r - 4))
    tiles.append(create_tile(hexagon_id, q - 4, r + 2))
    tiles.append(create_tile(hexagon_id, q - 3, r + 1))
    tiles.append(create_tile(hexagon_id, q - 2, r + 0))
    tiles.append(create_tile(hexagon_id, q - 1, r - 1))
    tiles.append(create_tile(hexagon_id, q + 0, r - 2))
    tiles.append(create_tile(hexagon_id, q + 1, r - 3))
    tiles.append(create_tile(hexagon_id, q + 2, r - 4))
    tiles.append(create_tile(hexagon_id, q - 4, r + 3))
    tiles.append(create_tile(hexagon_id, q - 3, r + 2))
    tiles.append(create_tile(hexagon_id, q - 2, r + 1))
    tiles.append(create_tile(hexagon_id, q - 1, r + 0))
    tiles.append(create_tile(hexagon_id, q + 0, r - 1))
    tiles.append(create_tile(hexagon_id, q + 1, r - 2))
    tiles.append(create_tile(hexagon_id, q + 2, r - 3))
    tiles.append(create_tile(hexagon_id, q + 3, r - 4))
    tiles.append(create_tile(hexagon_id, q - 4, r + 4))
    tiles.append(create_tile(hexagon_id, q - 3, r + 3))
    tiles.append(create_tile(hexagon_id, q - 2, r + 2))
    tiles.append(create_tile(hexagon_id, q - 1, r + 1))
    tiles.append(create_tile(hexagon_id, q - 0, r + 0))
    tiles.append(create_tile(hexagon_id, q + 1, r - 1))
    tiles.append(create_tile(hexagon_id, q + 2, r - 2))
    tiles.append(create_tile(hexagon_id, q + 3, r - 3))
    tiles.append(create_tile(hexagon_id, q + 4, r - 4))
    tiles.append(create_tile(hexagon_id, q - 3, r + 4))
    tiles.append(create_tile(hexagon_id, q - 2, r + 3))
    tiles.append(create_tile(hexagon_id, q - 1, r + 2))
    tiles.append(create_tile(hexagon_id, q + 0, r + 1))
    tiles.append(create_tile(hexagon_id, q + 1, r + 0))
    tiles.append(create_tile(hexagon_id, q + 2, r - 1))
    tiles.append(create_tile(hexagon_id, q + 3, r - 2))
    tiles.append(create_tile(hexagon_id, q + 4, r - 3))
    tiles.append(create_tile(hexagon_id, q - 2, r + 4))
    tiles.append(create_tile(hexagon_id, q - 1, r + 3))
    tiles.append(create_tile(hexagon_id, q + 0, r + 2))
    tiles.append(create_tile(hexagon_id, q + 1, r + 1))
    tiles.append(create_tile(hexagon_id, q + 2, r + 0))
    tiles.append(create_tile(hexagon_id, q + 3, r - 1))
    tiles.append(create_tile(hexagon_id, q + 4, r - 2))
    tiles.append(create_tile(hexagon_id, q - 1, r + 4))
    tiles.append(create_tile(hexagon_id, q + 0, r + 3))
    tiles.append(create_tile(hexagon_id, q + 1, r + 2))
    tiles.append(create_tile(hexagon_id, q + 2, r + 1))
    tiles.append(create_tile(hexagon_id, q + 3, r + 0))
    tiles.append(create_tile(hexagon_id, q + 4, r - 1))
    tiles.append(create_tile(hexagon_id, q + 0, r + 4))
    tiles.append(create_tile(hexagon_id, q + 1, r + 3))
    tiles.append(create_tile(hexagon_id, q + 2, r + 2))
    tiles.append(create_tile(hexagon_id, q + 3, r + 1))
    tiles.append(create_tile(hexagon_id, q + 4, r + 0))
    return tiles


class HexagonRest(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self):
        print("get hexagon")
        hexagons = []
        all_hexagons = Hexagon.query.all()
        lowest_hex = [0, 0]
        highest_hex = [0, 0]
        for h in all_hexagons:
            hexagon = h.serialize
            hexagons.append(hexagon)
            hex_q = hexagon["q"]
            hex_r = hexagon["r"]
            if hex_q < lowest_hex[0]:
                if hex_r < lowest_hex[1]:
                    lowest_hex[0] = hex_q
                    lowest_hex[1] = hex_r
            if hex_q > highest_hex[0]:
                if hex_r > highest_hex[1]:
                    highest_hex[0] = hex_q
                    highest_hex[1] = hex_r
        return {
            "hexagons": hexagons,
            "lowest_hex": lowest_hex,
            "highest_hex": highest_hex,
        }

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        json_data = request.get_json(force=True)
        print("post hexagon: %s" % json_data)
        q = json_data["q"]
        r = json_data["r"]
        if q is not None and r is not None:
            print("q: %s r: %s" % (q, r))
            hexagon = Hexagon.query.filter_by(q=q, r=r).first()

            if hexagon is None:
                hexagon = Hexagon(q=q, r=r)
                db.session.add(hexagon)
                db.session.commit()

                tiles = get_tiles(hexagon.id, q, r)
                for tile in tiles:
                    db.session.add(tile)
                db.session.commit()
                # For now, it will probably be q = 0, r = 0 but it's because of the tiles
                hexagon = Hexagon.query.filter_by(q=q, r=r).first()
                if hexagon is None:
                    print("wut")
                else:
                    print("hexagon has %s tiles" % len(hexagon.tiles))
                    return {"result": "hexagon created", "hexagon": hexagon.serialize}
            else:
                print("here we can update")
                print("hexagon has %s tiles" % len(hexagon.tiles))
                return {"result": "hexagon updated", "hexagon": hexagon.serialize}
        else:
            return {"result": "q or r is not provided. These are needed"}


api = Api(app_api)
api.add_resource(HexagonRest, "/api/v1.0/hexagon", endpoint="hexagon")
