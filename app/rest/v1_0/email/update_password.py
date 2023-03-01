import time
from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource

from app.models.user import User
from app.rest import app_api
from app import db
from app.rest.rest_util import get_failed_response
from app.util.email.email import EmailProcess
from app.util.email.reset_password_email import reset_password_email
from app.util.util import check_token


class UpdatePassword(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        print("post to password update")
        json_data = request.get_json(force=True)
        user = None
        if "access_token" in json_data:
            user = check_token(json_data["access_token"])
        else:
            return get_failed_response("invalid request")

        if not user:
            return get_failed_response("user not found")

        new_password = json_data["new_password"]
        if new_password is None:
            return get_failed_response("Invalid request")

        user.hash_password(new_password)
        db.session.add(user)
        db.session.commit()

        password_check_response = make_response({
            'result': True,
            'message': 'password updated!',
        }, 200)

        return password_check_response


api = Api(app_api)
api.add_resource(UpdatePassword, '/api/v1.0/password/update', endpoint='update_password')
