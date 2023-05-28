from urllib.parse import urlencode

import requests
from flask import redirect, request

from app.config import DevelopmentConfig, Config
from app.routes.login_user_origin import login_user_origin
from app.util.avatar.generate_avatar import AvatarProcess


def github_login(app):
    from app.util.util import get_user_tokens
    from app import db

    @app.route("/login/github", methods=["GET", "POST"])
    def login_github():
        print("attempting to login github :)")
        # base_url = DevelopmentConfig.GITHUB_API
        base_url = DevelopmentConfig.GITHUB_AUTHORIZE
        params = dict()
        params["client_id"] = DevelopmentConfig.GITHUB_CLIENT_ID

        url_params = urlencode(params)
        github_url = base_url + "/?" + url_params
        print("testing url: %s" % github_url)

        return redirect(github_url)

    @app.route("/login/github/callback", methods=["GET", "POST"])
    def github_callback():
        # Get authorization code Google sent back to you
        print("github callback!!!!")
        code = request.args.get("code")

        access_base_url = DevelopmentConfig.GITHUB_ACCESS
        params = dict()
        params["client_id"] = DevelopmentConfig.GITHUB_CLIENT_ID
        params["client_secret"] = DevelopmentConfig.GITHUB_CLIENT_SECRET
        params["code"] = code

        url_params = urlencode(params)
        github_post_url = access_base_url + "/?" + url_params

        headers = {
            "Accept": "application/json",
        }
        token_response = requests.post(github_post_url, headers=headers)

        github_response_json = token_response.json()

        headers_authorization = {
            "Accept": "application/json",
            "Authorization": "Bearer %s" % github_response_json["access_token"],
        }
        authorization_url = DevelopmentConfig.GITHUB_USER

        authorization_response = requests.get(
            authorization_url, headers=headers_authorization
        )

        github_user = authorization_response.json()

        users_name = github_user["login"]
        users_email = github_user["email"]

        user = login_user_origin(users_name, users_email, 2)

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
            world_url = request.base_url.replace(
                "/login/github/callback", "/worldaccess"
            )
            world_url_params = world_url + "?" + url_params
            return redirect(world_url_params)
        else:
            login_url = request.base_url.replace("/login/google/callback", "/")
            return redirect(login_url)
