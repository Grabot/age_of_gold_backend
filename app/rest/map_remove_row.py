from flask_restful import Api
from flask_restful import Resource

from app import DevelopmentConfig
from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db
from flask import request


class TestRest(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        return {
            "You have found a ": "test"
        }

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        json_data = request.get_json(force=True)
        password = json_data["password"]
        print("called the row remove endpoint")
        if password == DevelopmentConfig.PASSWORD_AGE_OF_GOLD:
            r = json_data["r"]
            if r:
                print("going to remove row %s" % r)
                hexagons = Hexagon.query.filter_by(r=r)
                for hexagon in hexagons:
                    tiles = hexagon.tiles
                    for tile in tiles:
                        db.session.delete(tile)
                db.session.commit()
                for hexagon in hexagons:
                    db.session.delete(hexagon)
                db.session.commit()
                print("map removed")
                return {"result": "Removed row %s" % r}
            else:
                return {"result": "Please provide a row"}
        else:
            print("map NOT removed")

        return {
            "You have found another ": "test"
        }


api = Api(app_api)
api.add_resource(TestRest, '/api/v1.0/map/remove/row', endpoint='remove_row')
