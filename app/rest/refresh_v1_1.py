from flask_cors import cross_origin
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User, refresh_user_token, get_user_tokens
from app.rest import app_api
from flask import request
from app import db


class Refresh(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    @cross_origin()
    def post(self):
        print("refresh?")
        json_data = request.get_json(force=True)
        access_token = json_data["access_token"]
        refresh_token = json_data["refresh_token"]

        if access_token is None or refresh_token is None:
            return {
                       'result': False,
                       'message': "User not authorized"
                   }, 400
        else:
            print("stuff present")
            user = refresh_user_token(access_token, refresh_token)
            if user:
                [access_token, refresh_token] = get_user_tokens(user)
                db.session.add(user)
                db.session.commit()
                return {
                    'result': True,
                    'message': 'user token successfully refreshed.',
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            else:
                return {
                           'result': False,
                           'message': "User not authorized"
                       }, 400


api = Api(app_api)
api.add_resource(Refresh, '/api/v1.0/refresh', endpoint='refresh_user')
