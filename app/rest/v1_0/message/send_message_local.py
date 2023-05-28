from datetime import datetime

from flask import make_response, request
from flask_restful import Api, Resource
from flask_socketio import emit

from app import DevelopmentConfig
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token, get_hex_room


class SendMessageLocal(Resource):
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
        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("an error occurred")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("an error occurred")

        now = datetime.utcnow()

        message_body = json_data["message"]
        hex_q = json_data["hex_q"]
        hex_r = json_data["hex_r"]
        tile_q = json_data["tile_q"]
        tile_r = json_data["tile_r"]
        room = get_hex_room(hex_q, hex_r)
        socket_response = {
            "user_name": user.username,
            "message": message_body,
            "tile_q": tile_q,
            "tile_r": tile_r,
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }

        emit(
            "send_message_local",
            socket_response,
            room=room,
            namespace=DevelopmentConfig.API_SOCK_NAMESPACE,
        )

        send_message_response = make_response(
            {
                "result": True,
            },
            200,
        )
        return send_message_response


api = Api(app_api)
api.add_resource(SendMessageLocal, "/api/v1.0/send/message/local", endpoint="send_message_local")
