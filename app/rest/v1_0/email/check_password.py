import time

from flask import make_response, request
from flask_restful import Api, Resource

from app import db
from app.models.user import User
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.email.email import EmailProcess
from app.util.email.reset_password_email import reset_password_email
from app.util.util import check_token


class CheckPassword(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        print("post to password check")
        json_data = request.get_json(force=True)
        user = None
        if "access_token" in json_data:
            user = check_token(json_data["access_token"])
        else:
            return get_failed_response("invalid request")

        if not user:
            return get_failed_response("user not found")

        password_check_response = make_response(
            {
                "result": True,
                "message": "password check was good",
            },
            200,
        )

        return password_check_response


api = Api(app_api)
api.add_resource(CheckPassword, "/api/v1.0/password/check", endpoint="check_password")
