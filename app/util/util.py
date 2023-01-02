import time

from authlib.jose import jwt
from authlib.jose.errors import DecodeError

from app.config import DevelopmentConfig
from app.models.user import User


def get_wraparounds(q, r):
    map_size = DevelopmentConfig.map_size
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
    user = User.query.filter_by(token=access_token).first()

    if user is None:
        print("access token not active")
        return None

    access = None
    refresh = None
    try:
        access = jwt.decode(access_token, DevelopmentConfig.jwk)
        refresh = jwt.decode(refresh_token, DevelopmentConfig.jwk)
    except DecodeError:
        print("decode error, big fail!")
        return None

    if not access or not refresh:
        print("big fail!")
        return None

    if refresh["exp"] < int(time.time()):
        print("refresh token not active")
        return None
    # It all needs to match before you send back new tokens
    if user.id == access["id"] and user.username == refresh["user_name"]:
        print("it's all good! Send more tokens")
        return user
    else:
        return None


def check_token(token):
    user = User.query.filter_by(token=token).first()
    if user is None or user.token_expiration < int(time.time()):
        return None
    return user


def get_user_tokens(user, access_expiration=3600, refresh_expiration=36000):
    # Create an access_token that the user can use to do user authentication
    token_expiration = int(time.time()) + access_expiration
    access_token = user.generate_auth_token(access_expiration).decode('ascii')
    # Create a refresh token that lasts longer that the user can use to generate a new access token
    refresh_token = user.generate_refresh_token(refresh_expiration).decode('ascii')
    # Only store the access token, refresh token is kept client side
    user.set_token(access_token)
    user.set_token_expiration(token_expiration)
    return [access_token, refresh_token]

