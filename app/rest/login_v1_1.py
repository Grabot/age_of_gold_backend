from flask_cors import cross_origin
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.models.user import User
from app.rest import app_api
from flask import request
from app import db
from app.util.util import get_user_tokens


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
            [access_token, refresh_token] = get_user_tokens(user)
            
            db.session.add(user)
            db.session.commit()
            return {
                'result': True,
                'message': 'user logged in successfully.',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.serialize
            }
        else:
            return {
                "result": False,
                "message": "user name or email not found"
            }


api = Api(app_api)
api.add_resource(Login, '/api/v1.0/login', endpoint='login_user')
