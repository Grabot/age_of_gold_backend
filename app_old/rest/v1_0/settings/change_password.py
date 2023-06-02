from flask import make_response, request
from flask_restful import Api, Resource

from app_old import db
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.util import check_token, get_auth_token


class ChangePassword(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        print("Changing password")
        json_data = request.get_json(force=True)
        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("Something went wrong")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("Something went wrong")

        new_password = json_data["password"]
        user.hash_password(new_password)

        db.session.add(user)
        db.session.commit()

        change_password_response = make_response(
            {
                "result": True,
                "message": new_password,
            },
            200,
        )

        return change_password_response


api = Api(app_api)
api.add_resource(ChangePassword, "/api/v1.0/change/password", endpoint="change_password")
