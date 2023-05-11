from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.friend import Friend
from app.models.user import User
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import get_auth_token, check_token
from app import db


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
        auth_token = get_auth_token(request.headers.get('Authorization'))
        if auth_token == '':
            return get_failed_response("an error occurred")

        user_from = check_token(auth_token)
        if not user_from:
            return get_failed_response("an error occurred")

        user_name = json_data["user_name"]
        user_befriend = User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
        if not user_befriend:
            return get_failed_response("an error occurred")

        friend_from = Friend.query.filter_by(user_id=user_from.id, friend_id=user_befriend.id).first()
        friend_befriend = Friend.query.filter_by(user_id=user_befriend.id, friend_id=user_from.id).first()
        if not friend_from or not friend_befriend:
            # They both have to exist if you're denying one
            return get_failed_response("something went wrong")
        else:
            friend_from.accepted = True
            friend_befriend.accepted = True
            db.session.add(friend_from)
            db.session.add(friend_befriend)
            db.session.commit()
            print("already friends")

        accept_request_response = make_response({
            'result': True,
            'message': "success"
        }, 200)
        return accept_request_response


api = Api(app_api)
api.add_resource(AcceptRequest, '/api/v1.0/accept/request', endpoint='accept_friend')
