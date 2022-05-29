from flask import request
from flask_restful import Api
from flask_restful import Resource

from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db


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
                for x in range(0, 61):
                    # TODO: make sure the q, r, s are correct
                    tile = Tile(hexagon_id=hexagon.id, type=0)
                    db.session.add(tile)
                db.session.commit()
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
