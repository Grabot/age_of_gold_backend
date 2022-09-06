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
        if password == DevelopmentConfig.PASSWORD_AGE_OF_GOLD:
            Tile.query.delete()
            Hexagon.query.delete()
            db.session.commit()
            print("map removed")
        else:
            print("map NOT removed")

        return {
            "You have found another ": "test"
        }


api = Api(app_api)
api.add_resource(TestRest, '/api/v1.0/map/remove', endpoint='remove')
