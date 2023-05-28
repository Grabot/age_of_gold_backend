import time

from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import desc

from app.models.message.global_message import GlobalMessage
from app.rest import app_api
from app.rest.rest_util import get_failed_response
from app.util.util import check_token, get_auth_token


class GetGlobalMessages(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self, page):
        if not page or not page.isdigit():
            return get_failed_response("an error occurred")

        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("an error occurred")

        user = check_token(auth_token)
        if not user:
            return get_failed_response("an error occurred")

        # We only retrieve the last 60 messages because we think there is no reason to scroll further back
        global_messages = (
            GlobalMessage.query.order_by(desc(GlobalMessage.timestamp))
            .paginate(page=int(page), per_page=60, error_out=False)
            .items
        )

        messages = [m.serialize for m in global_messages]

        get_message_response = make_response(
            {"result": True, "messages": messages}, 200
        )
        return get_message_response

    def put(self, page):
        pass

    def delete(self, page):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self, page):
        pass


api = Api(app_api)
api.add_resource(
    GetGlobalMessages,
    "/api/v1.0/get/message/global/<page>",
    endpoint="get_message_global",
)
