from flask import request
from flask_restful import Api, Resource

from app_old import db
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.util import check_token, get_user_tokens


class TokenLogin(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        json_data = request.get_json(force=True)
        user = None
        if "access_token" in json_data:
            user = check_token(json_data["access_token"])
        else:
            return get_failed_response("invalid request")

        if not user:
            return get_failed_response("user not found")
        else:
            # The access token was still good, refresh tokens and send back.
            [access_token, refresh_token] = get_user_tokens(user)

            db.session.add(user)
            db.session.commit()
            return {
                "result": True,
                "message": "user logged in successfully.",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.serialize,
            }, 200


api = Api(app_api)
api.add_resource(TokenLogin, "/api/v1.0/login/token", endpoint="token_login")