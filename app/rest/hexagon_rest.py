from flask import request
from flask_restful import Api
from flask_restful import Resource

from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db


def create_tile(hexagon_id, q, r, s):
    combined = q + r + s
    if combined != 0:
        print("BIG ERROR!!!!")
        print("q: %s, r: %s, s: %s" % (q, r, s))
        exit()
    return Tile(q=q, r=r, s=s, hexagon_id=hexagon_id, type=0)


def get_tiles(hexagon_id):
    # For now, we will define each of the tiles in the hexagon separate
    tiles = []
    tiles.append(create_tile(hexagon_id, -4, 0, 4))
    tiles.append(create_tile(hexagon_id, -3, -1, 4))
    tiles.append(create_tile(hexagon_id, -2, -2, 4))
    tiles.append(create_tile(hexagon_id, -1, -3, 4))
    tiles.append(create_tile(hexagon_id, 0, -4, 4))
    tiles.append(create_tile(hexagon_id, -4, 1, 3))
    tiles.append(create_tile(hexagon_id, -3, 0, 3))
    tiles.append(create_tile(hexagon_id, -2, -1, 3))
    tiles.append(create_tile(hexagon_id, -1, -2, 3))
    tiles.append(create_tile(hexagon_id, 0, -3, 3))
    tiles.append(create_tile(hexagon_id, 1, -4, 3))
    tiles.append(create_tile(hexagon_id, -4, 2, 2))
    tiles.append(create_tile(hexagon_id, -3, 1, 2))
    tiles.append(create_tile(hexagon_id, -2, 0, 2))
    tiles.append(create_tile(hexagon_id, -1, -1, 2))
    tiles.append(create_tile(hexagon_id, 0, -2, 2))
    tiles.append(create_tile(hexagon_id, 1, -3, 2))
    tiles.append(create_tile(hexagon_id, 2, -4, 2))
    tiles.append(create_tile(hexagon_id, -4, 3, 1))
    tiles.append(create_tile(hexagon_id, -3, 2, 1))
    tiles.append(create_tile(hexagon_id, -2, 1, 1))
    tiles.append(create_tile(hexagon_id, -1, 0, 1))
    tiles.append(create_tile(hexagon_id, 0, -1, 1))
    tiles.append(create_tile(hexagon_id, 1, -2, 1))
    tiles.append(create_tile(hexagon_id, 2, -3, 1))
    tiles.append(create_tile(hexagon_id, 3, -4, 1))
    tiles.append(create_tile(hexagon_id, -4, 4, 0))
    tiles.append(create_tile(hexagon_id, -3, 3, 0))
    tiles.append(create_tile(hexagon_id, -2, 2, 0))
    tiles.append(create_tile(hexagon_id, -1, 1, 0))
    tiles.append(create_tile(hexagon_id, -0, 0, 0))
    tiles.append(create_tile(hexagon_id, 1, -1, 0))
    tiles.append(create_tile(hexagon_id, 2, -2, 0))
    tiles.append(create_tile(hexagon_id, 3, -3, 0))
    tiles.append(create_tile(hexagon_id, 4, -4, 0))
    tiles.append(create_tile(hexagon_id, -3, 4, -1))
    tiles.append(create_tile(hexagon_id, -2, 3, -1))
    tiles.append(create_tile(hexagon_id, -1, 2, -1))
    tiles.append(create_tile(hexagon_id, 0, 1, -1))
    tiles.append(create_tile(hexagon_id, 1, 0, -1))
    tiles.append(create_tile(hexagon_id, 2, -1, -1))
    tiles.append(create_tile(hexagon_id, 3, -2, -1))
    tiles.append(create_tile(hexagon_id, 4, -3, -1))
    tiles.append(create_tile(hexagon_id, -2, 4, -2))
    tiles.append(create_tile(hexagon_id, -1, 3, -2))
    tiles.append(create_tile(hexagon_id, 0, 2, -2))
    tiles.append(create_tile(hexagon_id, 1, 1, -2))
    tiles.append(create_tile(hexagon_id, 2, 0, -2))
    tiles.append(create_tile(hexagon_id, 3, -1, -2))
    tiles.append(create_tile(hexagon_id, 4, -2, -2))
    tiles.append(create_tile(hexagon_id, -1, 4, -3))
    tiles.append(create_tile(hexagon_id, 0, 3, -3))
    tiles.append(create_tile(hexagon_id, 1, 2, -3))
    tiles.append(create_tile(hexagon_id, 2, 1, -3))
    tiles.append(create_tile(hexagon_id, 3, 0, -3))
    tiles.append(create_tile(hexagon_id, 4, -1, -3))
    tiles.append(create_tile(hexagon_id, 0, 4, -4))
    tiles.append(create_tile(hexagon_id, 1, 3, -4))
    tiles.append(create_tile(hexagon_id, 2, 2, -4))
    tiles.append(create_tile(hexagon_id, 3, 1, -4))
    tiles.append(create_tile(hexagon_id, 4, 0, -4))
    return tiles


class HexagonRest(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        print("get hexagon")
        return {"Hello": "Hexagon"}

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
        s = json_data["s"]
        if q is not None and r is not None and s is not None:
            print("q: %s r: %s s: %s" % (q, r, s))
            hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()

            if hexagon is None:
                hexagon = Hexagon(q=q, r=r, s=s)
                db.session.add(hexagon)
                db.session.commit()
                tiles = get_tiles(hexagon.id)
                for tile in tiles:
                    db.session.add(tile)
                db.session.commit()
                # For now, it will probably be q = 0, r = 0 and s = 0 but it's because of the tiles
                hexagon = Hexagon.query.filter_by(q=q, r=r, s=s).first()
                if hexagon is None:
                    print("wut")
                else:
                    print("hexagon has %s tiles" % len(hexagon.tiles))
                    return {
                        "result": "hexagon created",
                        "hexagon": hexagon.serialize
                    }
            else:
                print("here we can update")
                print("hexagon has %s tiles" % len(hexagon.tiles))
                return {
                    "result": "hexagon updated",
                    "hexagon": hexagon.serialize
                }
        else:
            return {"result": "q, r or s is not provided. These are needed"}


api = Api(app_api)
api.add_resource(HexagonRest, '/api/v1.0/hexagon', endpoint='hexagon')
