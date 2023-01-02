from flask_cors import cross_origin
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User
from app.rest import app_api
from flask import request, make_response
from app import db
from app.util.util import get_user_tokens


class Test(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        print("reached test endpoint")
        # print(request.headers)
        test_response = make_response({
            'result': True,
            'message': 'This is a test endpoint',
            'access_token': "",
            'refresh_token': ""
        })

        return test_response


api = Api(app_api)
api.add_resource(Test, '/api/v1.0/test', endpoint='test')
