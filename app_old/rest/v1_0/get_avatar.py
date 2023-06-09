import base64
import os

from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import func

from app_old.config import Config
from app_old.models.user import User
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response


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
        json_data = request.get_json(force=True)
        user_name = json_data["user_name"]
        user_avatar = User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
        if not user_avatar:
            return get_failed_response("user not found")

        file_folder = Config.UPLOAD_FOLDER
        if user_avatar.is_default():
            file_name = user_avatar.avatar_filename_default()
        else:
            file_name = user_avatar.avatar_filename_small()

        file_path = os.path.join(file_folder, "%s.png" % file_name)
        if not os.path.isfile(file_path):
            return get_failed_response("An error occurred")
        else:
            with open(file_path, "rb") as fd:
                image_as_base64 = base64.encodebytes(fd.read()).decode()

            avatar_response = make_response({"result": True, "avatar": image_as_base64}, 200)

            return avatar_response


api = Api(app_api)
api.add_resource(GetAvatar, "/api/v1.0/get/avatar", endpoint="get_avatar")