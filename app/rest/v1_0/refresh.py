from flask_restful import Api
from flask_restful import Resource
from app.rest import app_api
from flask import request
from app import db
from app.rest.rest_util import get_failed_response
from app.util.util import refresh_user_token, get_user_tokens


class Refresh(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        print("refresh?")
        json_data = request.get_json(force=True)
        access_token = json_data["access_token"]
        refresh_token = json_data["refresh_token"]

        if access_token is None or refresh_token is None:
            return {
                       'result': False,
                       'message': "User not authorized"
                   }, 200
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
                    'refresh_token': refresh_token,
                    'user': user.serialize
                }, 200
            else:
                return get_failed_response("Authorization failed")


api = Api(app_api)
api.add_resource(Refresh, '/api/v1.0/refresh', endpoint='refresh_user')
