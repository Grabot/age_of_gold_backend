from flask_restful import Api
from flask_restful import Resource
from app import mail
from app.config import Config
from app.rest import app_api
from flask import make_response
from flask_mail import Message
from app.util.email.verification_email import verification_email


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
