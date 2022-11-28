from flask_cors import cross_origin
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User
from app.rest import app_api
from flask import request
from app import db


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

        # Create an access_token that the user can use to do user authentication
        access_token = user.generate_auth_token(3600).decode('ascii')
        # Create a refresh token that lasts longer that the user can use to generate a new access token
        refresh_token = user.generate_refresh_token(36000).decode('ascii')
        # Only store the access token, refresh token is kept client side
        user.set_token(access_token)

        db.session.add(user)
        db.session.commit()
        return {
            'result': True,
            'message': 'user created successfully.',
            'access_token': access_token,
            'refresh_token': refresh_token
        }


api = Api(app_api)
api.add_resource(Register, '/api/v1.0/register', endpoint='register_user')
