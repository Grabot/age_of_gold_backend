import base64
import os

from flask import make_response, request
from flask_restful import Api, Resource

from app import db
from app.config import Config
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token


class ResetAvatar(Resource):
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

        user_avatar = check_token(auth_token)
        if not user_avatar:
            return get_failed_response("Something went wrong")

        user_avatar.set_default_avatar(True)
        db.session.add(user_avatar)
        db.session.commit()

        file_folder = Config.UPLOAD_FOLDER
        file_name = user_avatar.avatar_filename_default()
        file_path = os.path.join(file_folder, "%s.png" % file_name)

        if not os.path.isfile(file_path):
            return get_failed_response("An error occurred")
        else:
            with open(file_path, "rb") as fd:
                image_as_base64 = base64.encodebytes(fd.read()).decode()

            reset_avatar_response = make_response(
                {
                    "result": True,
                    "message": image_as_base64,
                },
                200,
            )

            return reset_avatar_response


api = Api(app_api)
api.add_resource(ResetAvatar, "/api/v1.0/reset/avatar", endpoint="reset_avatar")
