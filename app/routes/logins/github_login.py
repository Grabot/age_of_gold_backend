from flask import redirect, request
import requests
from app.config import DevelopmentConfig
from urllib.parse import urlencode
from app.routes.login_user_origin import login_user_origin


#TODO: turn it to api endpoints?
def github_login(app):

    @app.route("/login/github", methods=['GET', 'POST'])
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

    @app.route("/login/github/callback", methods=['GET', 'POST'])
    def github_callback():
        # Get authorization code Google sent back to you
        print("github callback!!!!")
        code = request.args.get("code")
        print("code: %s" % code)

        access_base_url = DevelopmentConfig.GITHUB_ACCESS
        params = dict()
        params["client_id"] = DevelopmentConfig.GITHUB_CLIENT_ID
        params["client_secret"] = DevelopmentConfig.GITHUB_CLIENT_SECRET
        params["code"] = code

        url_params = urlencode(params)
        github_post_url = access_base_url + "/?" + url_params

        print("github post url: %s" % github_post_url)

        headers = {
            "Accept": "application/json",
        }
        token_response = requests.post(
            github_post_url,
            headers=headers
        )
        print("testing url 2: %s" % token_response)
        print("testing url 3: %s" % token_response.url)
        print("testing url 3: %s" % token_response.text)
        print("testing url 4: %s" % token_response.json())
        github_response_json = token_response.json()
        print("testing url 5: %s" % github_response_json)
        print("testing url 6: %s" % github_response_json["access_token"])
        print("testing url 7: %s" % github_response_json["token_type"])
        print("testing url 8: %s" % github_response_json["scope"])

        headers_authorization = {
            "Accept": "application/json",
            "Authorization": "Bearer %s" % github_response_json["access_token"]
        }
        authorization_url = DevelopmentConfig.GITHUB_USER

        authorization_response = requests.get(
            authorization_url,
            headers=headers_authorization
        )
        print("final?")
        print(authorization_response)
        print(authorization_response.json())

        github_user = authorization_response.json()

        users_name = github_user["login"]
        users_email = github_user["email"]
        picture = github_user["avatar_url"]
        print("user verified!")
        print(users_email)
        print(picture)
        print(users_name)

        login_user_origin(users_name, users_email, 2)

        # Send user to the world
        world_url = request.base_url.replace("/login/github/callback", "/world")
        return redirect(world_url)
