from flask import make_response, request
from flask_restful import Api, Resource
from sqlalchemy import func

from app_old.models.user import User
from app_old.rest import app_api
from app_old.rest.rest_util import get_failed_response
from app_old.util.util import check_token, get_auth_token


class SearchFriend(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    # noinspection PyMethodMayBeStatic
    def post(self):
        print("search for friend")
        json_data = request.get_json(force=True)
        auth_token = get_auth_token(request.headers.get("Authorization"))
        if auth_token == "":
            return get_failed_response("an error occurred")

        user_from = check_token(auth_token)
        if not user_from:
            return get_failed_response("an error occurred")

        user_search = json_data["username"]
        print("search for friend: %s" % user_search)
        search_user = User.query.filter(
            func.lower(User.username) == func.lower(user_search)
        ).first()
        if not search_user:
            return get_failed_response("an error occurred")
        else:
            print("found someone, returning")
            search_user_response = make_response(
                {"result": True, "friend": search_user.serialize_get}, 200
            )
            return search_user_response


api = Api(app_api)
api.add_resource(SearchFriend, "/api/v1.0/search/friend", endpoint="search_friend")
