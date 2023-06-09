from datetime import datetime

from flask import make_response, request
from flask_restful import Api, Resource
from flask_socketio import emit
from sqlalchemy import func

from app_old import DevelopmentConfig, db
from app_old.models.friend import Friend
from app_old.models.message.personal_message import PersonalMessage
from app_old.models.user import User
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.util import check_token, get_auth_token


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
        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("an error occurred")

        from_user = check_token(auth_token)
        if not from_user:
            return get_failed_response("an error occurred")

        message_body = json_data["message"]
        to_user = json_data["to_user"].lower()
        user_send = User.query.filter(func.lower(User.username) == func.lower(to_user)).first()
        if not user_send:
            return get_failed_response("user not found")

        # Retrieve the friend object belonging to who we're sending it to.
        friend_send = Friend.query.filter_by(user_id=user_send.id, friend_id=from_user.id).first()
        if not friend_send:
            # If there is no friend object we will create both of them.
            # After creation, add an unread message to who we're messaging
            friend_send = user_send.befriend(from_user)
            from_friend = from_user.befriend(user_send)
            db.session.add(from_friend)

        friend_send.add_unread_message()
        db.session.add(friend_send)

        now = datetime.utcnow()

        # I could add the Friend object on the message,
        # but it's not needed for storage or retrieval, so we won't
        new_personal_message = PersonalMessage(
            body=message_body,
            user_id=from_user.id,
            receiver_id=user_send.id,
            timestamp=now,
        )

        room_from = "room_%s" % from_user.id
        room_to = "room_%s" % user_send.id
        socket_response = {
            "from_user": from_user.username,
            "sender_id": from_user.id,
            "to_user": user_send.username,
            "message": message_body,
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }

        emit(
            "send_message_personal",
            socket_response,
            room=room_from,
            namespace=DevelopmentConfig.API_SOCK_NAMESPACE,
        )
        emit(
            "send_message_personal",
            socket_response,
            room=room_to,
            namespace=DevelopmentConfig.API_SOCK_NAMESPACE,
        )

        db.session.add(new_personal_message)
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
    SendMessagePersonal,
    "/api/v1.0/send/message/personal",
    endpoint="send_message_personal",
)