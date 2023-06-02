from flask import make_response
from flask_mail import Message
from flask_restful import Api, Resource

from app_old import mail
from app_old.config import Config
from app_old.rest import app_api
from app_old.util.email.verification_email import verification_email


class Test(Resource):
    def get(self):
        msg = Message(
            "test subject",
            sender=Config.MAIL_USERNAME,
            recipients=["SanderKools@gmail.com"],
        )
        msg.html = verification_email
        mail.send(msg)
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def post(self):
        print("reached test endpoint")
        # print(request.headers)
        test_response = make_response(
            {
                "result": True,
                "message": "This is a test endpoint",
                "access_token": "",
                "refresh_token": "",
            }
        )

        return test_response


api = Api(app_api)
api.add_resource(Test, "/api/v1.0/test", endpoint="test")
