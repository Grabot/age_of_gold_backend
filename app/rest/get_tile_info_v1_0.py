from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource

from app.models.tile import Tile
from app.rest import app_api


def response_get_tile_info_failed(message):
    get_tile_info_response = make_response({
        'result': False,
        'message': message,
    }, 200)
    return get_tile_info_response


class GetTileInfo(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        json_data = request.get_json(force=True)
        tile_q = json_data["q"]
        tile_r = json_data["r"]
        print("tile_q: %s tile_r: %s" % (tile_q, tile_r))
        if not tile_q or not tile_r or not tile_q.lstrip("-").isdigit() or not tile_r.lstrip("-").isdigit():
            response_get_tile_info_failed("error occurred")
        tile = Tile.query.filter_by(q=tile_q, r=tile_r).first()
        if not tile:
            response_get_tile_info_failed("error occurred")

        get_tile_info_response = make_response({
            'result': True,
            'tile': tile.serialize_full
        }, 200)
        return get_tile_info_response


api = Api(app_api)
api.add_resource(GetTileInfo, '/api/v1.0/tile/get/info', endpoint='get_tile_info')