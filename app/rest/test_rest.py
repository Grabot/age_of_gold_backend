from flask_restful import Api
from flask_restful import Resource
from app.rest import app_api
from app import r


class TestRest(Resource):

    # noinspection PyMethodMayBeStatic
    def get(self):
        r.publish('messages', "quick test")
        return {
            "You have found a ": "test"
        }

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        pass


api = Api(app_api)
api.add_resource(TestRest, '/api/v1.0/test', endpoint='test')
