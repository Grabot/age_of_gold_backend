from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from flask_socketio import emit

from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db, DevelopmentConfig
import json

from app.util.util import get_auth_token, check_token


def response_tile_change_failed(message):
    tile_change_response = make_response({
        'result': False,
        'message': message,
    }, 200)
    return tile_change_response


class TileChange(Resource):

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
        auth_token = get_auth_token(request.headers.get('Authorization'))
        if auth_token == '':
            return response_tile_change_failed("back to login")

        user = check_token(auth_token)
        if not user:
            return response_tile_change_failed("back to login")

        if not user.can_change_tile_type():
            return response_tile_change_failed("not allowed")

        tile_q = json_data["q"]
        tile_r = json_data["r"]
        tile_type = json_data["type"]
        if not tile_q or not tile_r or not tile_type or not tile_q.lstrip("-").isdigit() \
                or not tile_r.lstrip("-").isdigit() or not tile_type.lstrip("-").isdigit():
            return response_tile_change_failed("error occurred")

        tile = Tile.query.filter_by(q=int(tile_q), r=int(tile_r)).first()
        if not tile:
            return response_tile_change_failed("error occurred")

        tile_hexagon = Hexagon.query.filter_by(id=tile.hexagon_id).first()
        if not tile_hexagon:
            return response_tile_change_failed("error occurred")

        user.lock_tile_setting(1)
        tile.update_tile_info(int(tile_type), user.id)
        db.session.add(tile)
        db.session.add(user)
        room = "%s_%s" % (tile_hexagon.q, tile_hexagon.r)
        # Emit the results to the hex room.
        emit("change_tile_type_success", tile.serialize_full, room=room, namespace=DevelopmentConfig.API_SOCK_NAMESPACE)

        # We can get all the tiles and re-write the tiles_detail
        # But we will just look for the correct tile in the existing string
        # and update just that one.
        prev_details = json.loads(tile_hexagon.tiles_detail)
        for tile_detail in prev_details:
            if tile_detail["q"] == tile.q and tile_detail["r"] == tile.r:
                tile_detail["type"] = tile.type
        tile_hexagon.tiles_detail = json.dumps(prev_details)
        db.session.add(tile_hexagon)
        db.session.commit()

        tile_change_response = make_response({
            'result': True,
        }, 200)
        return tile_change_response


api = Api(app_api)
api.add_resource(TileChange, '/api/v1.0/tile/change', endpoint='change_tile')
