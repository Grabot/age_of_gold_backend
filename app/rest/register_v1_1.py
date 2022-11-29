from flask_cors import cross_origin
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User
from app.rest import app_api
from flask import request
from app import db
from app.util.util import get_user_tokens


class Register(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    @cross_origin()
    def post(self):
        print("register?")
        json_data = request.get_json(force=True)
        email = json_data["email"]
        password = json_data["password"]
        user_name = json_data["user_name"]

        if email is None or password is None or user_name is None:
            return {
                       'result': False,
                       'message': "Invalid request"
                   }, 400
        if User.query.filter(func.lower(User.username) == func.lower(user_name)).first() is not None:
            return {
                'result': False,
                'message': "User is already taken, please choose a different one."
            }, 400

        user = User(
            username=user_name,
            email=email
        )
        user.hash_password(password)

        [access_token, refresh_token] = get_user_tokens(user)

        db.session.add(user)
        db.session.commit()
        return {
            'result': True,
            'message': 'user created successfully.',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.serialize
        }


api = Api(app_api)
api.add_resource(Register, '/api/v1.0/register', endpoint='register_user')
