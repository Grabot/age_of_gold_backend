from flask import request, make_response
from flask_restful import Api
from flask_restful import Resource
from app.config import Config
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.email.email import EmailProcess
from app.util.email.verification_email import verification_email
from app.util.util import get_auth_token, check_token
from app import db
import time


# TODO: Test
class VerifyEmail(Resource):

    def get(self):
        auth_token = get_auth_token(request.headers.get('Authorization'))
        if auth_token == '':
            return get_failed_response("back to login")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("back to login")

        print("attempting to send an email to %s" % user.email)

        expiration_time = 18000  # 5 hours
        token_expiration = int(time.time()) + expiration_time
        reset_token = user.generate_auth_token(expiration_time).decode('ascii')
        subject = "Age of Gold - Verify your email"
        body = verification_email.format(base_url=Config.BASE_URL, token=reset_token)
        p = EmailProcess(user.email, subject, body)
        p.start()

        user.set_token(reset_token)
        user.set_token_expiration(token_expiration)
        db.session.add(user)
        db.session.commit()

        verify_email_response = make_response({
            'result': True,
            'message': 'Email verification email send?',
        }, 200)

        return verify_email_response

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        pass


api = Api(app_api)
api.add_resource(VerifyEmail, '/api/v1.0/verify', endpoint='verify_user')
