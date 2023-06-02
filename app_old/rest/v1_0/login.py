from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import func

from app_old import db
from app_old.models.user import User
from app_old.rest import app_api
from app_old.util.util import get_user_tokens


class Login(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        json_data = request.get_json(force=True)
        user = None
        if "email" in json_data:
            email = json_data["email"]
            password = json_data["password"]
            user = (
                User.query.filter_by(origin=0)
                .filter(func.lower(User.email) == func.lower(email))
                .first()
            )
        elif "user_name" in json_data:
            user_name = json_data["user_name"]
            password = json_data["password"]
            user = (
                User.query.filter_by(origin=0)
                .filter(func.lower(User.username) == func.lower(user_name))
                .first()
            )
        else:
            return {"result": False, "message": "invalid request"}

        if user:
            # Valid login, we refresh the token for this user.
            [access_token, refresh_token] = get_user_tokens(user)
            if not user.verify_password(password):
                return make_response({"result": False, "message": "password not correct"}, 200)
            db.session.add(user)
            db.session.commit()

            login_response = make_response(
                {
                    "result": True,
                    "message": "user logged in successfully.",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user.serialize,
                }
            )

            return login_response
        else:
            return {"result": False, "message": "user name or email not found"}


api = Api(app_api)
api.add_resource(Login, "/api/v1.0/login", endpoint="login_user")
