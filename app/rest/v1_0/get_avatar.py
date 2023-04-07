from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
import os
from app.models.user import User
from app.rest.rest_util import get_failed_response
from app.rest import app_api
import base64


class GetAvatar(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        print("I'm about the get the avatar")
        json_data = request.get_json(force=True)
        user_name = json_data["user_name"]
        user_get = User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
        if not user_get:
            return get_failed_response("user not found")
        print("Found a user")

        filename = user_get.avatar_filename()
        file_path = os.path.join("/app", "static", "uploads", "%s.png" % filename)
        if not os.path.isfile(file_path):
            return get_failed_response("An error occurred")
        else:
            with open(file_path, 'rb') as fd:
                image_as_base64 = base64.encodebytes(fd.read()).decode()

            avatar_response = make_response({
                'result': True,
                'avatar': image_as_base64,
            }, 200)

            return avatar_response


api = Api(app_api)
api.add_resource(GetAvatar, '/api/v1.0/get/avatar', endpoint='get_avatar')
