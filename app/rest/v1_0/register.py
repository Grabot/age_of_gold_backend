from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User
from app.rest import app_api
from flask import request, make_response
from app import db
from app.rest.rest_util import get_failed_response
from app.util.util import get_user_tokens


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

        if User.query.filter(func.lower(User.username) == func.lower(user_name)).first() is not None:
            return get_failed_response("User is already taken, please choose a different one.")

        user = User(
            username=user_name,
            email=email,
            origin=0
        )
        user.hash_password(password)

        [access_token, refresh_token] = get_user_tokens(user)

        db.session.add(user)
        db.session.commit()

        login_response = make_response({
            'result': True,
            'message': 'user created successfully.',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.serialize
        }, 200)

        return login_response


api = Api(app_api)
api.add_resource(Register, '/api/v1.0/register', endpoint='register_user')
