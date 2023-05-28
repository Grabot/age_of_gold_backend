import time

from flask import make_response, request
from flask_restful import Api, Resource

from app import db
from app.config import Config
from app.models.user import User
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.email.email import EmailProcess
from app.util.email.verification_email import verification_email
from app.util.util import check_token, decode_token, get_auth_token


class VerifyEmail(Resource):
    def get(self):
        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("back to login")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("user not found")

        expiration_time = 18000  # 5 hours
        reset_token = user.generate_auth_token(expiration_time).decode("ascii")
        subject = "Age of Gold - Verify your email"
        body = verification_email.format(base_url=Config.BASE_URL, token=reset_token)
        p = EmailProcess(user.email, subject, body)
        p.start()

        # We generate an auth token, but we don't store it on the user.
        # For the verification we will just attempt to decode it and check the id.

        verify_email_response = make_response(
            {
                "result": True,
                "message": "Email verification email send",
            },
            200,
        )

        return verify_email_response

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        json_data = request.get_json(force=True)
        if "access_token" in json_data:
            decoded_token = decode_token(json_data["access_token"])
        else:
            return get_failed_response("invalid request")

        if "id" not in decoded_token or "exp" not in decoded_token:
            return get_failed_response("invalid token")

        user_id = decoded_token["id"]
        expiration = decoded_token["exp"]

        if not user_id or not expiration:
            return get_failed_response("no user found")

        if expiration < int(time.time()):
            return get_failed_response("verification email expired")

        user = User.query.filter_by(id=user_id).first()

        if not user:
            return get_failed_response("no user found")

        if user.is_verified():
            verify_email_response = make_response(
                {
                    "result": True,
                    "message": "Email %s has already been verified!" % user.email,
                },
                200,
            )

        else:
            user.verify_user()
            db.session.add(user)
            db.session.commit()

            verify_email_response = make_response(
                {
                    "result": True,
                    "message": "Email %s is verified!" % user.email,
                },
                200,
            )

        return verify_email_response


api = Api(app_api)
api.add_resource(VerifyEmail, "/api/v1.0/email/verification", endpoint="verify_email")
