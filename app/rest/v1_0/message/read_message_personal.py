from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import func

from app import db
from app.models.friend import Friend
from app.models.user import User
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token


class ReadPersonalMessages(Resource):
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

        user_from = check_token(auth_token)
        if not user_from:
            return get_failed_response("an error occurred")

        read_user = json_data["read_user"]
        user_read = User.query.filter(
            func.lower(User.username) == func.lower(read_user)
        ).first()
        if not user_read:
            return get_failed_response("user not found")

        friend = Friend.query.filter_by(
            user_id=user_from.id, friend_id=user_read.id
        ).first()
        if not friend:
            return get_failed_response("something went wrong")

        print("unread messages: %s" % friend.unread_messages)

        friend.unread_messages = 0
        db.session.add(friend)
        db.session.commit()

        get_message_response = make_response(
            {"result": True, "message": "success"}, 200
        )
        return get_message_response


api = Api(app_api)
api.add_resource(
    ReadPersonalMessages,
    "/api/v1.0/read/message/personal",
    endpoint="read_message_personal",
)
