from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import func

from app_old.models.message.personal_message import PersonalMessage
from app_old.models.user import User
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.util import check_token, get_auth_token


class GetPersonalMessages(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self, page):
        pass

    def put(self, page):
        pass

    def delete(self, page):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self, page):
        json_data = request.get_json(force=True)

        if not page or not page.isdigit():
            return get_failed_response("an error occurred")

        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("an error occurred")
        user_from = check_token(auth_token)
        if not user_from:
            return get_failed_response("an error occurred")

        to_user = json_data["from_user"]
        user_to = User.query.filter(func.lower(User.username) == func.lower(to_user)).first()
        if not user_to:
            return get_failed_response("user not found")
        # We only retrieve the last 60 messages because there is no reason to read further back,
        # unless the user wants to
        personal_messages = (
            PersonalMessage.query.filter_by(user_id=user_from.id, receiver_id=user_to.id)
            .union(PersonalMessage.query.filter_by(user_id=user_to.id, receiver_id=user_from.id))
            .order_by(PersonalMessage.timestamp.desc())
            .paginate(page=int(page), per_page=60, error_out=False)
            .items
        )

        messages = [m.serialize for m in personal_messages]

        get_message_response = make_response({"result": True, "messages": messages}, 200)
        return get_message_response


api = Api(app_api)
api.add_resource(
    GetPersonalMessages,
    "/api/v1.0/get/message/personal/<page>",
    endpoint="get_message_personal",
)
