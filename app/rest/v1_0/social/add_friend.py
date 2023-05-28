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


class AddFriend(Resource):
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
        print("friend %s is going to add %s as a new friend!" % (user_from.username, user_name))
        user_befriend = User.query.filter(
            func.lower(User.username) == func.lower(user_name)
        ).first()
        if not user_befriend:
            return get_failed_response("an error occurred")
        friend_from = Friend.query.filter_by(
            user_id=user_from.id, friend_id=user_befriend.id
        ).first()
        if not friend_from:
            print("they were not friends yet, so going to create the friend objects")
            # not friends yet, create Friend objects, always for both users!
            friend_befriend = user_befriend.befriend(user_from)
            friend_from = user_from.befriend(user_befriend)
        else:
            friend_befriend = Friend.query.filter_by(
                user_id=user_befriend.id, friend_id=user_from.id
            ).first()
            if not friend_befriend:
                return get_failed_response("an error occurred")
            print("already friends")

        # set requested indicator
        if friend_from.requested is True and friend_befriend.requested is False:
            print("request is already sent!")
            add_friend_response = make_response(
                {"result": True, "message": "request already sent"}, 200
            )
            return add_friend_response
        elif friend_befriend.requested is True and friend_from.requested is False:
            print("The other person has sent a request")
            # This is if a friend request is send by the other person and now this person sends one
            # Let's assume they both accept to be friends
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

            add_friend_response = make_response(
                {"result": True, "message": "They are now friends"}, 200
            )
            return add_friend_response
        else:
            print("Successfully sent a request")
            friend_from.requested = True
            friend_befriend.requested = False
            db.session.add(friend_from)
            db.session.add(friend_befriend)
            db.session.commit()
            # Emit on the room of the person. If that person is online they will see the request
            socket_response = {
                "from": user_from.serialize_minimal,
            }
            room_to = "room_%s" % user_befriend.id
            emit(
                "received_friend_request",
                socket_response,
                room=room_to,
                namespace=DevelopmentConfig.API_SOCK_NAMESPACE,
            )

            add_friend_response = make_response({"result": True, "message": "success"}, 200)
            return add_friend_response


api = Api(app_api)
api.add_resource(AddFriend, "/api/v1.0/add/friend", endpoint="add_friend")
