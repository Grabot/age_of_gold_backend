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


class DenyRequest(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("an error occurred")

        user_from = check_token(auth_token)
        if not user_from:
            return get_failed_response("an error occurred")

        json_data = request.get_json(force=True)
        user_name = json_data["user_name"]
        user_de_befriend = User.query.filter(
            func.lower(User.username) == func.lower(user_name)
        ).first()
        if not user_de_befriend:
            return get_failed_response("an error occurred")

        friend_from = Friend.query.filter_by(
            user_id=user_from.id, friend_id=user_de_befriend.id
        ).first()
        friend_befriend = Friend.query.filter_by(
            user_id=user_de_befriend.id, friend_id=user_from.id
        ).first()
        if not friend_from or not friend_befriend:
            # They both have to exist if you're denying one
            return get_failed_response("no friend request found")
        else:
            friend_from.requested = None
            friend_befriend.requested = None

            if friend_from.accepted:
                # We also set the accepted back to false. This can be a denied request or an unfriend.
                friend_from.accepted = False
                friend_befriend.accepted = False
                # TODO: Add message that they are unfriended?

            db.session.add(friend_from)
            db.session.add(friend_befriend)
            db.session.commit()

            # Emit on the room of the befriend person. If that person is online he will see the request
            socket_response = {
                "from": user_from.username,
            }
            room_to = "room_%s" % user_de_befriend.id
            emit(
                "denied_friend",
                socket_response,
                room=room_to,
                namespace=DevelopmentConfig.API_SOCK_NAMESPACE,
            )

            deny_request_response = make_response(
                {"result": True, "message": "success"}, 200
            )
            return deny_request_response


api = Api(app_api)
api.add_resource(DenyRequest, "/api/v1.0/deny/request", endpoint="deny_request")
