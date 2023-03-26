from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from flask_socketio import emit
from sqlalchemy import func

from app.models.post import Post
from app.models.user import User
from app.rest import app_api
from app import db, DevelopmentConfig
from app.rest.rest_util import get_failed_response
from app.util.util import get_auth_token, check_token


class SendMessagePersonal(Resource):

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

        from_user = check_token(auth_token)
        if not from_user:
            return get_failed_response("an error occurred")

        message_body = json_data["message"]
        to_user = json_data["to_user"].lower()
        user_send = User.query.filter(func.lower(User.username) == func.lower(to_user)).first()
        if not user_send:
            return get_failed_response("user not found")

        room_from = "room_%s" % from_user.id
        room_to = "room_%s" % user_send.id
        socket_response = {
            "user_name": from_user.username,
            "message": message_body
        }

        emit("send_message_personal", socket_response, room=room_from, namespace=DevelopmentConfig.API_SOCK_NAMESPACE)
        emit("send_message_personal", socket_response, room=room_to, namespace=DevelopmentConfig.API_SOCK_NAMESPACE)

        send_message_response = make_response({
            'result': True,
        }, 200)
        return send_message_response


api = Api(app_api)
api.add_resource(SendMessagePersonal, '/api/v1.0/send/message/personal', endpoint='send_message_personal')
