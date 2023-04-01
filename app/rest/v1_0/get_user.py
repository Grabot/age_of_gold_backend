from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User
from app.rest.rest_util import get_failed_response
from app.rest import app_api
from app.util.util import get_auth_token
from app.util.util import check_token


class GetUser(Resource):

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
            return get_failed_response("back to login")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("back to login")

        if not user.can_change_tile_type():
            return get_failed_response("not allowed")

        user_name = json_data["user_name"]
        user_get = User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
        if not user_get:
            return get_failed_response("user not found")

        get_user_response = make_response({
            'result': True,
            'user': user_get.serialize
        }, 200)
        return get_user_response


api = Api(app_api)
api.add_resource(GetUser, '/api/v1.0/get/user', endpoint='get_user')