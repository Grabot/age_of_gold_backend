from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import func

from app import db
from app.models.user import User
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token


class ChangeUsername(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        print("Changing username")
        json_data = request.get_json(force=True)
        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("Something went wrong")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("Something went wrong")

        new_username = json_data["username"]
        if (
            User.query.filter(
                func.lower(User.username) == func.lower(new_username)
            ).first()
            is not None
        ):
            return get_failed_response(
                "User is already taken, please choose a different one."
            )

        print(
            "Everything went fine, going to change %s to %s"
            % (user.username, new_username)
        )
        user.set_new_username(new_username)
        db.session.add(user)
        db.session.commit()

        change_username_response = make_response(
            {
                "result": True,
                "message": new_username,
            },
            200,
        )

        return change_username_response


api = Api(app_api)
api.add_resource(
    ChangeUsername, "/api/v1.0/change/username", endpoint="change_username"
)
