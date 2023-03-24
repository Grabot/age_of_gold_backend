import time
from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from sqlalchemy import func
from app.config import Config
from app.models.user import User
from app.rest import app_api
from app import db
from app.rest.rest_util import get_failed_response
from app.util.email.email import EmailProcess
from app.util.email.reset_password_email import reset_password_email


class ResetPassword(Resource):

    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        print("post to password reset")
        json_data = request.get_json(force=True)
        email = json_data["email"]
        if email is None:
            return get_failed_response("error occurred")

        user = User.query.filter_by(origin=0).filter(func.lower(User.email) == func.lower(email)).first()
        if not user:
            return get_failed_response("no account found using this email")

        expiration_time = 18000  # 5 hours
        token_expiration = int(time.time()) + expiration_time
        reset_token = user.generate_auth_token(expiration_time).decode('ascii')

        print("attempting to send an email to %s" % email)
        subject = "Age of Gold - Change your password"
        body = reset_password_email.format(base_url=Config.BASE_URL, token=reset_token)
        p = EmailProcess(email, subject, body)
        p.start()
        print("thread started")
        user.set_token(reset_token)
        user.set_token_expiration(token_expiration)
        db.session.add(user)
        db.session.commit()

        password_reset_response = make_response({
            'result': True,
            'message': 'password reset mail is send',
        }, 200)

        return password_reset_response


api = Api(app_api)
api.add_resource(ResetPassword, '/api/v1.0/password/reset', endpoint='reset_password')
