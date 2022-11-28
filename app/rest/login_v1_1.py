from flask_cors import cross_origin
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User
from app.rest import app_api
from flask import request
from app import db


class Login(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    @cross_origin()
    def post(self):
        print("login?")
        json_data = request.get_json(force=True)
        user = None
        if "email" in json_data:
            email = json_data["email"]
            password = json_data["password"]
            print("email: %s" % email)
            print("password: %s" % password)
            print("json data: %s" % json_data)
            user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
        elif "user_name" in json_data:
            user_name = json_data["user_name"]
            password = json_data["password"]
            print("user: %s" % user_name)
            print("password: %s" % password)
            print("json data: %s" % json_data)
            user = User.query.filter(func.lower(User.username) == func.lower(user_name)).first()
        else:
            return {
                "result": False,
                "message": "invalid request"
            }

        if user:
            print("found a user")
            # Valid login, we refresh the token for this user.
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
                'message': 'user logged in successfully.',
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        else:
            return {
                "result": False,
                "message": "user name or email not found"
            }


api = Api(app_api)
api.add_resource(Login, '/api/v1.0/login', endpoint='login_user')
