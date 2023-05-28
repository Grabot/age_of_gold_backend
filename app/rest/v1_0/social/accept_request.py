from flask import make_response, request
from flask_restful import Api, Resource
from flask_socketio import emit
from sqlalchemy import func

from app import DevelopmentConfig, db
from app.models.friend import Friend
from app.models.user import User
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token


class AcceptRequest(Resource):
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

        user_name = json_data["user_name"]
        user_befriend = User.query.filter(
            func.lower(User.username) == func.lower(user_name)
        ).first()
        if not user_befriend:
            return get_failed_response("an error occurred")

        friend_from = Friend.query.filter_by(
            user_id=user_from.id, friend_id=user_befriend.id
        ).first()
        friend_befriend = Friend.query.filter_by(
            user_id=user_befriend.id, friend_id=user_from.id
        ).first()
        if not friend_from or not friend_befriend:
            # They both have to exist if you're accepting one
            return get_failed_response("something went wrong")

        friend_from.accepted = True
        friend_befriend.accepted = True
        db.session.add(friend_from)
        db.session.add(friend_befriend)
        db.session.commit()

        socket_response = {
            "from": user_from.username,
        }
        room_to = "room_%s" % user_befriend.id
        emit(
            "accept_friend_request",
            socket_response,
            room=room_to,
            namespace=DevelopmentConfig.API_SOCK_NAMESPACE,
        )

        accept_request_response = make_response({"result": True, "message": "success"}, 200)
        return accept_request_response


api = Api(app_api)
api.add_resource(AcceptRequest, "/api/v1.0/accept/request", endpoint="accept_friend")
