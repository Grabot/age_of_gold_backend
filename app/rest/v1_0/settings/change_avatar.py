from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource

from app import db
from app.config import Config
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import get_auth_token, check_token
import os
import io
import base64
import stat
from PIL import Image


class ChangeAvatar(Resource):

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
            return get_failed_response("Something went wrong")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("Something went wrong")

        new_avatar = json_data["avatar"]
        new_avatar_small = json_data["avatar_small"]

        # Turn base64 string to PIL image file
        new_avatar_pil = Image.open(io.BytesIO(base64.b64decode(new_avatar)))
        new_avatar_small_pil = Image.open(io.BytesIO(base64.b64decode(new_avatar_small)))

        # Get the file name and path
        file_folder = Config.UPLOAD_FOLDER
        file_name = user.avatar_filename()
        file_name_small = user.avatar_filename() + "_small"
        # Store the image under the same hash but without the "default".
        file_path = os.path.join(file_folder, "%s.png" % file_name)
        file_path_small = os.path.join(file_folder, "%s.png" % file_name_small)

        new_avatar_pil.save(file_path)
        new_avatar_small_pil.save(file_path_small)
        os.chmod(file_path, stat.S_IRWXO)
        os.chmod(file_path_small, stat.S_IRWXO)

        user.set_default_avatar(False)
        db.session.add(user)
        db.session.commit()

        avatar_response = make_response({
            'result': True,
            'message': "success",
        }, 200)

        return avatar_response


api = Api(app_api)
api.add_resource(ChangeAvatar, '/api/v1.0/change/avatar', endpoint='change_avatar')
