from datetime import datetime

from flask import make_response, request
from flask_restful import Api, Resource
from flask_socketio import emit

from app_old import DevelopmentConfig
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.util import check_token, get_auth_token


class SendMessageGuild(Resource):
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
        # guild_name = json_data["guild_name"]
        # guild_id = 0
        # TODO: Add guild functionality with rooms
        # room = "guild_room_%s" % guild_id
        socket_response = {
            "user_name": user.username,
            "sender_id": user.id,
            "message": message_body,
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }

        emit(
            "send_message_guild",
            socket_response,
            broadcast=True,
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
api.add_resource(SendMessageGuild, "/api/v1.0/send/message/guild", endpoint="send_message_guild")