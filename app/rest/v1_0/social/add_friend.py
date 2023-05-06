from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func

from app import db
from app.models.friend import Friend
from app.models.user import User
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import get_auth_token, check_token


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
        auth_token = get_auth_token(request.headers.get('Authorization'))
        if auth_token == '':
            return get_failed_response("an error occurred")

        user_from = check_token(auth_token)
        if not user_from:
            return get_failed_response("an error occurred")

        user_name = json_data["username"]
        print("friend %s is going to add %s as a new friend!" % (user_from.username, user_name))
        user_befriend = User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
        friends = Friend.query.filter_by(user_id=user_from.id, friend_id=user_befriend.id).first()
        if not friends:
            print("they were not friends yet, so going to create the friend objects")
            # not friends yet, create Friend objects, always for both users!
            user_befriend.befriend(user_from)
            user_from.befriend(user_befriend)
            db.session.commit()
        else:
            print("already friends")

        get_message_response = make_response({
            'result': True,
        }, 200)
        return get_message_response


api = Api(app_api)
api.add_resource(AddFriend, '/api/v1.0/add/friend', endpoint='add_friend')
