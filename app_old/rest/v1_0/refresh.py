from flask import request
from flask_restful import Api, Resource

from app_old import db
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.util import get_user_tokens, refresh_user_token


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
            return {"result": False, "message": "User not authorized"}, 200
        else:
            print("stuff present")
            user = refresh_user_token(access_token, refresh_token)
            if user:
                [access_token, refresh_token] = get_user_tokens(user)
                db.session.add(user)
                db.session.commit()
                return {
                    "result": True,
                    "message": "user token successfully refreshed.",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user.serialize,
                }, 200
            else:
                return get_failed_response("Authorization failed")


api = Api(app_api)
api.add_resource(Refresh, "/api/v1.0/refresh", endpoint="refresh_user")
