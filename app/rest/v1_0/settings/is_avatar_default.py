import base64
import io
import os
import stat

from flask import make_response, request
from flask_restful import Api, Resource
from PIL import Image

from app import db
from app.config import Config
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token


class IsAvatarDefault(Resource):
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
            return get_failed_response("Something went wrong")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("Something went wrong")

        avatar_response = make_response(
            {
                "result": user.is_default(),
            },
            200,
        )

        return avatar_response


api = Api(app_api)
api.add_resource(
    IsAvatarDefault, "/api/v1.0/get/avatar/default", endpoint="get_avatar_default"
)
