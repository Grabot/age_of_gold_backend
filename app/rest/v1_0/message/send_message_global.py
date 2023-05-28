from datetime import datetime

from flask import make_response, request
from flask_restful import Api, Resource
from flask_socketio import emit

from app import DevelopmentConfig, db
from app.models.message.global_message import GlobalMessage
from app.models.post import Post
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token


class SendMessageGlobal(Resource):
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

        message_body = json_data["message"]
        users_username = user.username

        now = datetime.utcnow()

        socket_response = {
            "user_name": users_username,
            "message": message_body,
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }

        emit(
            "send_message_global",
            socket_response,
            broadcast=True,
            namespace=DevelopmentConfig.API_SOCK_NAMESPACE,
        )

        new_global_message = GlobalMessage(
            body=message_body, sender_name=users_username, timestamp=now
        )
        db.session.add(new_global_message)
        db.session.commit()

        send_message_response = make_response(
            {
                "result": True,
            },
            200,
        )
        return send_message_response


api = Api(app_api)
api.add_resource(
    SendMessageGlobal, "/api/v1.0/send/message/global", endpoint="send_message_global"
)
