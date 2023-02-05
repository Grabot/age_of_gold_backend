from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from flask_socketio import emit
from sqlalchemy import tuple_

from app.models.hexagon import Hexagon
from app.models.tile import Tile
from app.rest import app_api
from app import db, DevelopmentConfig
import json

from app.util.util import get_auth_token, check_token, get_wraparounds


def response_get_hexagon_failed(message):
    get_hexagon_response = make_response({
        'result': False,
        'message': message,
    }, 200)
    return get_hexagon_response


class GetHexagon(Resource):

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
            return response_get_hexagon_failed("back to login")

        user = check_token(auth_token)
        if not user:
            return response_get_hexagon_failed("back to login")

        # The json should have 1 or more hexagons
        hexagons = json.loads(json_data["hexagons"])
        if not hexagons:
            return response_get_hexagon_failed("error occurred")

        map_size = DevelopmentConfig.map_size
        is_wrapped = False
        hex_retrieve = []
        hex_retrieve_wrapped = []
        for hexagon in hexagons:
            hex_q = hexagon["q"]
            hex_r = hexagon["r"]
            # If the hex is out of the map bounds we want it to loop around
            if hex_q < -map_size or hex_q > map_size or hex_r < -map_size or hex_r > map_size:
                [hex_q, wrap_q, hex_r, wrap_r] = get_wraparounds(hex_q, hex_r)

                hex_retrieve_wrapped.append([hex_q, hex_r, wrap_q, wrap_r])
                is_wrapped = True
            hex_retrieve.append([hex_q, hex_r])
        hexes_return = []
        if hex_retrieve:
            hexes = db.session.query(Hexagon).filter(tuple_(Hexagon.q, Hexagon.r).in_(hex_retrieve)).all()
            for hexagon in hexes:
                return_hexagon = hexagon.serialize
                if is_wrapped:
                    for hex_wrapped in hex_retrieve_wrapped:
                        if hexagon.q == hex_wrapped[0] and hexagon.r == hex_wrapped[1]:
                            return_hexagon["wraparound"] = {
                                "q": hex_wrapped[2],
                                "r": hex_wrapped[3]
                            }
                            break
                hexes_return.append(return_hexagon)

        get_hexagon_response = make_response({
            'result': True,
            'hexagons': hexes_return,
        }, 200)
        return get_hexagon_response


api = Api(app_api)
api.add_resource(GetHexagon, '/api/v1.0/hexagon/get', endpoint='get_hexagon')
