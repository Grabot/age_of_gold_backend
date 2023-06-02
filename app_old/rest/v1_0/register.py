from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import func

from app_old import db
from app_old.config import Config
from app_old.models.user import User
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.avatar.generate_avatar import AvatarProcess
from app_old.util.util import get_user_tokens


class Register(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        json_data = request.get_json(force=True)
        email = json_data["email"]
        user_name = json_data["user_name"]
        password = json_data["password"]

        if email is None or password is None or user_name is None:
            return get_failed_response("Invalid request")

        if (
            User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
            is not None
        ):
            return get_failed_response("User is already taken, please choose a different one.")

        if (
            User.query.filter_by(origin=0)
            .filter(func.lower(User.email) == func.lower(email))
            .first()
            is not None
        ):
            return get_failed_response("This email has already been used to create an account")

        user = User(username=user_name, email=email, origin=0)
        avatar = AvatarProcess(user.avatar_filename(), Config.UPLOAD_FOLDER)
        avatar.start()
        user.hash_password(password)

        [access_token, refresh_token] = get_user_tokens(user)

        db.session.add(user)
        db.session.commit()

        login_response = make_response(
            {
                "result": True,
                "message": "user created successfully.",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.serialize,
            },
            200,
        )

        return login_response


api = Api(app_api)
api.add_resource(Register, "/api/v1.0/register", endpoint="register_user")
