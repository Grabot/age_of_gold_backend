from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update
from util.util import check_token, get_auth_token

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.models.message import GlobalMessage


class ChangeUsernameRequest(BaseModel):
    username: str


@api_router_v1.post("/change/username", status_code=200)
async def change_username(
    change_username_request: ChangeUsernameRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("change password")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        get_failed_response("An error occurred", response)

    new_username = change_username_request.username
    user_statement = select(User).where(func.lower(User.username) == new_username.lower())
    results = await db.execute(user_statement)
    result = results.first()
    if result is not None:
        return get_failed_response(
            "User is already taken, please choose a different one.", response
        )

    print("Everything went fine, going to change %s to %s" % (user.username, new_username))
    user.set_new_username(new_username)
    # update global messages

    message_update_statement = (
        update(GlobalMessage)
        .values(sender_name=new_username)
        .where(GlobalMessage.sender_id == user.id)
    )
    print("update statement: %s" % message_update_statement)
    results = await db.execute(message_update_statement)
    print("results: %s" % results)

    db.add(user)
    await db.commit()

    return {
        "result": True,
        "message": new_username,
    }


# from flask import make_response, request
# from flask_restful import Api, Resource
# from sqlalchemy import func
#
# from app_old import db
# from app_old.models.message.global_message import GlobalMessage
# from app_old.models.user import User
# from app_old.rest import app_api
# from app_old.rest.rest_util import get_failed_response
# from app_old.util.util import check_token, get_auth_token
#
#
# class ChangeUsername(Resource):
#     def get(self):
#         pass
#
#     def put(self):
#         pass
#
#     def delete(self):
#         pass
#
#     # noinspection PyMethodMayBeStatic
#     def post(self):
#         print("Changing username")
#         json_data = request.get_json(force=True)
#         auth_token = get_auth_token(request.headers.get("Authorization"))
#         if auth_token == "":
#             return get_failed_response("Something went wrong")
#
#         user = check_token(auth_token)
#         if not user:
#             return get_failed_response("Something went wrong")
#
#         new_username = json_data["username"]
#         if (
#             User.query.filter(func.lower(User.username) == func.lower(new_username)).first()
#             is not None
#         ):
#             return get_failed_response("User is already taken, please choose a different one.")
#
#         print("Everything went fine, going to change %s to %s" % (user.username, new_username))
#         user.set_new_username(new_username)
#         # update global messages
#         message_update = (
#             GlobalMessage.update()
#             .values(sender_name=new_username)
#             .where(GlobalMessage.sender_id == user.id)
#         )
#         db.session.add(message_update)
#
#         db.session.add(user)
#         db.session.commit()
#
#         change_username_response = make_response(
#             {
#                 "result": True,
#                 "message": new_username,
#             },
#             200,
#         )
#
#         return change_username_response
#
#
# api = Api(app_api)
# api.add_resource(ChangeUsername, "/api/v1.0/change/username", endpoint="change_username")
