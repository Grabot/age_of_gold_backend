from flask_restful import Api
from flask_restful import Resource
from app.rest import app_api
from flask import request
from app import db
from app.util.util import get_user_tokens, check_token


class TokenLogin(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        print("TokenLogin?")
        json_data = request.get_json(force=True)
        user = None
        if "access_token" in json_data:
            user = check_token(json_data["access_token"])
        else:
            return {
                "result": False,
                "message": "invalid request"
            }, 200

        if not user:
            return {
                "result": False,
                "message": "user not found"
            }, 200
        else:
            # The access token was still good, refresh tokens and send back.
            [access_token, refresh_token] = get_user_tokens(user)

            db.session.add(user)
            db.session.commit()
            return {
                'result': True,
                'message': 'user logged in successfully.',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.serialize
            }, 200


api = Api(app_api)
api.add_resource(TokenLogin, '/api/v1.0/login/token', endpoint='token_login')
