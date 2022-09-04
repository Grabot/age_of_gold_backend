from flask_restful import Api
from flask_restful import Resource
from app.rest import app_api


class TestRest(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        return {
            "You have found a ": "test"
        }

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        return {
            "You have found another ": "test"
        }


api = Api(app_api)
api.add_resource(TestRest, '/api/v1.0/test', endpoint='test')
