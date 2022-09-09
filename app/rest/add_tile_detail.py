from flask import request
from flask_restful import Api
from flask_restful import Resource
from app.models.hexagon import Hexagon
from app.rest import app_api
from app import db
import json


class MapRest(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        all_hexagons = Hexagon.query.all()
        for hexagon in all_hexagons:
            print("doing hexagon %s_%s" % (hexagon.q, hexagon.r))
            tiles = hexagon.tiles
            tiles_info = []
            for tile in tiles:
                tiles_info.append(tile.serialize)
            print("some detail: %s" % type(tiles_info))
            hexagon.tiles_detail = json.dumps(tiles_info)
            db.session.add(hexagon)
            db.session.commit()
        return {"Hello": "Map"}

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        json_data = request.get_json(force=True)
        r = json_data["r"]
        if r or r == 0:
            hexagons = Hexagon.query.filter_by(r=r)
            for hexagon in hexagons:
                print("doing hexagon %s_%s" % (hexagon.q, hexagon.r))
                tiles = hexagon.tiles
                tiles_info = []
                for tile in tiles:
                    tiles_info.append(tile.serialize)
                hexagon.tiles_detail = json.dumps(tiles_info)
                db.session.add(hexagon)
                db.session.commit()
            return {"result": "row %s is updated" % r}
        else:
            return {"result": "no row given"}


api = Api(app_api)
api.add_resource(MapRest, '/api/v1.0/tile/detail', endpoint='add_tile_detail')
