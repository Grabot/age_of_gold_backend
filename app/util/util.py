import time
from typing import Optional

from authlib.jose import jwt
from authlib.jose.errors import DecodeError
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import User


def get_wraparounds(q, r):
    map_size = settings.map_size
    wrap_q = 0
    wrap_r = 0
    if q < -map_size:
        while q < -map_size:
            q = q + (2 * map_size + 1)
            wrap_q -= 1
    if q > map_size:
        while q > map_size:
            q = q - (2 * map_size + 1)
            wrap_q += 1
    if r < -map_size:
        while r < -map_size:
            r = r + (2 * map_size + 1)
            wrap_r -= 1
    if r > map_size:
        while r > map_size:
            r = r - (2 * map_size + 1)
            wrap_r += 1
    return [q, wrap_q, r, wrap_r]


def refresh_user_token(access_token, refresh_token):
    # The access token should be active
    # TODO: fix this for new User object
    return None
    # user = User.query.filter_by(token=access_token).first()
    #
    # if user is None:
    #     print("access token not active")
    #     return None
    #
    # access = None
    # refresh = None
    # try:
    #     access = jwt.decode(access_token, DevelopmentConfig.jwk)
    #     refresh = jwt.decode(refresh_token, DevelopmentConfig.jwk)
    # except DecodeError:
    #     print("decode error, big fail!")
    #     return None
    #
    # if not access or not refresh:
    #     print("big fail!")
    #     return None
    #
    # if refresh["exp"] < int(time.time()):
    #     print("refresh token not active")
    #     return None
    # # It all needs to match before you send back new tokens
    # if user.id == access["id"] and user.username == refresh["user_name"]:
    #     print("it's all good! Send more tokens")
    #     return user
    # else:
    #     return None


async def check_token(db: AsyncSession, token) -> Optional[User]:
    print(f"checking token! {token}")
    user_statement = select(User).filter_by(token=token)
    results = await db.execute(user_statement)
    result = results.first()
    if result is None:
        return None
    print(f"found a user {result}")
    user = result.User
    print(f"found a user {user}")
    if user.token_expiration < int(time.time()):
        return None
    else:
        return user


def get_user_tokens(user: User, access_expiration=3600, refresh_expiration=36000):
    # Create an access_token that the user can use to do user authentication
    token_expiration = int(time.time()) + access_expiration
    access_token = user.generate_auth_token(access_expiration).decode("ascii")
    # Create a refresh token that lasts longer that the user can use to generate a new access token
    refresh_token = user.generate_refresh_token(refresh_expiration).decode("ascii")
    # Only store the access token, refresh token is kept client side
    print("setting token")
    print(access_token)
    print(refresh_token)
    print(token_expiration)
    user.set_token(access_token)
    user.set_token_expiration(token_expiration)
    print("set tokens on user object")
    return [access_token, refresh_token]


def get_auth_token(auth_header):
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ""
    return auth_token


def decode_token(token):
    try:
        id_token = jwt.decode(token, settings.jwk)
    except DecodeError:
        return

    if id_token is None:
        return

    return id_token


def get_hex_room(hex_q, hex_r):
    room = "%s_%s" % (hex_q, hex_r)
    return room
