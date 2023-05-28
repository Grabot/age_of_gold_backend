from base64 import b64encode
from urllib.parse import urlencode

import requests
from flask import redirect, request

from app.config import Config, DevelopmentConfig
from app.routes.login_user_origin import login_user_origin
from app.util.avatar.generate_avatar import AvatarProcess


def reddit_login(app):
    from app import db
    from app.util.util import get_user_tokens

    @app.route("/login/reddit", methods=["GET", "POST"])
    def login_reddit():
        print("attempting to login reddit :)")
        # TODO: correct endpoint?
        reddit_base_url = DevelopmentConfig.REDDIT_AUTHORIZE
        params = dict()
        params["client_id"] = DevelopmentConfig.REDDIT_CLIENT_ID
        params["duration"] = "temporary"
        params["redirect_uri"] = DevelopmentConfig.REDDIT_REDIRECT
        params["response_type"] = "code"
        params["scope"] = "identity"
        params["state"] = "x"

        url_params = urlencode(params)
        reddit_url = reddit_base_url + "/?" + url_params
        print("testing url: %s" % reddit_url)

        return redirect(reddit_url)

    @app.route("/login/reddit/callback", methods=["GET", "POST"])
    def reddit_callback():
        # Get authorization code Google sent back to you
        print("reddit callback!!!!")
        code = request.args.get("code")
        state = request.args.get("state")

        access_base_url = DevelopmentConfig.REDDIT_ACCESS

        token_post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DevelopmentConfig.REDDIT_REDIRECT,
        }

        encoded_authorization = "%s:%s" % (
            DevelopmentConfig.REDDIT_CLIENT_ID,
            DevelopmentConfig.REDDIT_CLIENT_SECRET,
        )

        http_auth = b64encode(encoded_authorization.encode("utf-8")).decode("utf-8")
        authorization = "Basic %s" % http_auth
        headers = {
            "Accept": "application/json",
            "User-agent": "age of gold login bot 0.1",
            "Authorization": authorization,
        }

        token_response = requests.post(access_base_url, headers=headers, data=token_post_data)

        reddit_response_json = token_response.json()

        headers_authorization = {
            "Accept": "application/json",
            "User-agent": "app of gold login bot 0.1",
            "Authorization": "bearer %s" % reddit_response_json["access_token"],
        }
        authorization_url = DevelopmentConfig.REDDIT_USER

        authorization_response = requests.get(authorization_url, headers=headers_authorization)

        reddit_user = authorization_response.json()

        users_name = reddit_user["name"]
        users_email = "%s@reddit.com" % users_name  # Reddit gives no email?

        user = login_user_origin(users_name, users_email, 3)

        if user:
            avatar = AvatarProcess(user.avatar_filename(), Config.UPLOAD_FOLDER)
            avatar.start()

            [access_token, refresh_token] = get_user_tokens(user, 30, 60)

            db.session.add(user)
            db.session.commit()

            params = dict()
            params["access_token"] = access_token
            params["refresh_token"] = refresh_token
            url_params = urlencode(params)

            # Send user to the world
            world_url = request.base_url.replace("/login/reddit/callback", "/worldaccess")
            world_url_params = world_url + "?" + url_params
            # Send user to the world
            return redirect(world_url_params)
        else:
            login_url = request.base_url.replace("/login/google/callback", "/")
            return redirect(login_url)
