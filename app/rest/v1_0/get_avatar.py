from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func

from app.models.user import User
from app.rest.rest_util import get_failed_response
from app.models.tile import Tile
from app.rest import app_api
import base64


class GetAvatar(Resource):

    # noinspection PyMethodMayBeStatic
    # TODO: check and/or store email with lowercase?
    def get(self, filename=None):
        with open('/app/static/uploads/%s' % filename, 'rb') as fd:
            image_as_base64_html = base64.encodebytes(fd.read()).decode()
        return image_as_base64_html

    def put(self, filename=None):
        pass

    def delete(self, filename=None):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self, filename=None):
        json_data = request.get_json(force=True)
        user_name = json_data["user_name"]
        user_get = User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
        if not user_get:
            return get_failed_response("user not found")

        with open('/app/static/uploads/%s' % user_get.email, 'rb') as fd:
            image_as_base64_html = f"""
           <img src="data:image/png;base64,{base64.encodebytes(fd.read()).decode()}">"""
        login_response = make_response({
            'result': True,
            'avatar': image_as_base64_html,
        }, 200)

        return login_response


api = Api(app_api)
api.add_resource(GetAvatar, '/api/v1.0/get/avatar/<filename>', endpoint='get_avatar')
