from flask import make_response, request
from flask_restful import Api, Resource

from app_old.models.tile import Tile
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response


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
        if (
            not tile_q
            or not tile_r
            or not tile_q.lstrip("-").isdigit()
            or not tile_r.lstrip("-").isdigit()
        ):
            return get_failed_response("error occurred")
        tile = Tile.query.filter_by(q=tile_q, r=tile_r).first()
        if not tile:
            return get_failed_response("error occurred")

        get_tile_info_response = make_response({"result": True, "tile": tile.serialize_full}, 200)
        return get_tile_info_response


api = Api(app_api)
api.add_resource(GetTileInfo, "/api/v1.0/tile/get/info", endpoint="get_tile_info")
