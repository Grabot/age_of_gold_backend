from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from app.rest import app_api


class ChangeAvatar(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        print("Changing avatar")
        json_data = request.get_json(force=True)
        avatar_response = make_response({
            'result': True,
        }, 200)

        return avatar_response


api = Api(app_api)
api.add_resource(ChangeAvatar, '/api/v1.0/change/avatar', endpoint='change_avatar')
