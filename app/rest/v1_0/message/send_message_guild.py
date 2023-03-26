from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from flask_socketio import emit
from app.models.post import Post
from app.rest import app_api
from app import db, DevelopmentConfig
from app.rest.rest_util import get_failed_response
from app.util.util import get_auth_token, check_token, get_hex_room


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
        auth_token = get_auth_token(request.headers.get('Authorization'))
        if auth_token == '':
            return get_failed_response("an error occurred")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("an error occurred")

        message_body = json_data["message"]
        guild_name = json_data["guild_name"]
        guild_id = 0
        # TODO: Add guild functionality with rooms
        room = "guild_room_%s" % guild_id
        socket_response = {
            "user_name": user.username,
            "message": message_body,
        }

        emit("send_message_guild", socket_response, broadcast=True, namespace=DevelopmentConfig.API_SOCK_NAMESPACE)

        send_message_response = make_response({
            'result': True,
        }, 200)
        return send_message_response


api = Api(app_api)
api.add_resource(SendMessageGuild, '/api/v1.0/send/message/guild', endpoint='send_message_guild')
