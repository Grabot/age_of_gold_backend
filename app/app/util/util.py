import time
from typing import Optional

from authlib.jose import jwt
from authlib.jose.errors import DecodeError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.config.config import settings
from app.models import User, UserToken


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


async def delete_user_token_and_return(db: AsyncSession, user_token, return_value: Optional[User]):
    await db.delete(user_token)
    await db.commit()
    return return_value


async def refresh_user_token(db: AsyncSession, access_token, refresh_token):
    token_statement = (
        select(UserToken)
        .filter_by(access_token=access_token)
        .filter_by(refresh_token=refresh_token)
    )
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None

    user_token: UserToken = result_token.UserToken
    if user_token.refresh_token_expiration < int(time.time()):
        return await delete_user_token_and_return(db, user_token, None)

    user_statement = (
        select(User)
        .filter_by(id=user_token.user_id)
        .options(selectinload(User.friends))
        .options(selectinload(User.guild))
    )
    user_results = await db.execute(user_statement)
    user_result = user_results.first()
    if user_result is None:
        return await delete_user_token_and_return(db, user_token, None)
    user = user_result.User

    if user_token.token_expiration > int(time.time()):
        return await delete_user_token_and_return(db, user_token, user)
    try:
        access = jwt.decode(access_token, settings.jwk)
        refresh = jwt.decode(refresh_token, settings.jwk)
    except DecodeError:
        return await delete_user_token_and_return(db, user_token, None)

    if not access or not refresh:
        return await delete_user_token_and_return(db, user_token, None)

    # do the refresh time check again, just in case.
    if refresh["exp"] < int(time.time()):
        return await delete_user_token_and_return(db, user_token, None)

    # It all needs to match before you accept the login
    if user.id == access["id"] and user.username == refresh["user_name"]:
        return await delete_user_token_and_return(db, user_token, user)
    else:
        return await delete_user_token_and_return(db, user_token, None)


async def check_token(db: AsyncSession, token, retrieve_full=False) -> Optional[User]:
    token_statement = select(UserToken).filter_by(access_token=token)
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None

    user_token: UserToken = result_token.UserToken
    if user_token.token_expiration < int(time.time()):
        return None
    if retrieve_full:
        user_statement = (
            select(User)
            .filter_by(id=user_token.user_id)
            .options(selectinload(User.friends))
            .options(selectinload(User.guild))
        )
    else:
        user_statement = select(User).filter_by(id=user_token.user_id)
    results = await db.execute(user_statement)
    result = results.first()
    if result is None:
        return None
    user = result.User
    return user


def get_user_tokens(user: User, access_expiration=1800, refresh_expiration=345600):
    # Create an access_token that the user can use to do user authentication
    token_expiration = int(time.time()) + access_expiration
    refresh_token_expiration = int(time.time()) + refresh_expiration
    access_token = user.generate_auth_token(access_expiration).decode("ascii")
    # Create a refresh token that lasts longer that the user can use to generate a new access token
    # right now choose 30 minutes and 4 days for access and refresh token.
    refresh_token = user.generate_refresh_token(refresh_expiration).decode("ascii")
    # Only store the access token, refresh token is kept client side
    print("creating user token 3")
    print(f"expiration: {token_expiration}")
    print(f"refresh_expiration: {refresh_expiration}")
    user_token = UserToken(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiration=token_expiration,
        refresh_token_expiration=refresh_token_expiration,
    )
    return user_token


def get_auth_token(auth_header):
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ""
    return auth_token


def get_hex_room(hex_q, hex_r):
    room = "%s_%s" % (hex_q, hex_r)
    return room
