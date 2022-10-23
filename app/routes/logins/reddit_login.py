from flask import redirect, request
import requests
from app.config import DevelopmentConfig
from urllib.parse import urlencode
from base64 import b64encode


#TODO: turn it to api endpoints?
def reddit_login(app):

    @app.route("/api/reddit/test/login", methods=['GET', 'POST'])
    def login_reddit():
        print("attempting to login reddit :)")
        # TODO: correct endpoint?
        # base_url = DevelopmentConfig.REDDIT_AUTHORIZE
        base_url = "https://www.reddit.com/api/v1/authorize"
        params = dict()
        params["client_id"] = DevelopmentConfig.REDDIT_CLIENT_ID
        params["duration"] = "temporary"
        params["redirect_uri"] = "http://127.0.0.1:5000/api/reddit/test/login/callback"
        params["response_type"] = "code"
        params["scope"] = "identity"
        params["state"] = "x"

        url_params = urlencode(params)
        reddit_url = base_url + "/?" + url_params
        print("testing url: %s" % reddit_url)

        return redirect(reddit_url)

    from app import db
    from app.models.user import User

    @app.route("/api/reddit/test/login/callback", methods=['GET', 'POST'])
    def reddit_callback():
        # Get authorization code Google sent back to you
        print("reddit callback!!!!")
        code = request.args.get("code")
        print("code: %s" % code)
        state = request.args.get("state")
        print("state: %s" % state)

        # access_base_url = DevelopmentConfig.REDDIT_ACCESS
        access_base_url = "https://www.reddit.com/api/v1/access_token"

        print("reddit post url: %s" % access_base_url)

        token_post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://127.0.0.1:5000/api/reddit/test/login/callback"
        }

        encoded_authorzation = "%s:%s" % (DevelopmentConfig.REDDIT_CLIENT_ID, DevelopmentConfig.REDDIT_CLIENT_SECRET)
        print("encoded authorization: %s" % encoded_authorzation)

        http_auth = b64encode(encoded_authorzation.encode("utf-8")).decode("utf-8")
        headers = {
            "Accept": "application/json",
            "Authorization": "Basic " + http_auth
        }

        print("url: %s" % access_base_url)
        print("headers: %s" % headers)
        print("data: %s" % token_post_data)
        token_response = requests.post(
            access_base_url,
            headers=headers,
            data=token_post_data
        )

        # TODO: 429( too many requests?!) probeer later nog eens
        print("testing url 2: %s" % token_response)
        print("testing url 3: %s" % token_response.url)

        print("testing url 3: %s" % token_response.text)
    #     print("testing url 4: %s" % token_response.json())
    #     github_response_json = token_response.json()
    #     print("testing url 5: %s" % github_response_json)
    #     print("testing url 6: %s" % github_response_json["access_token"])
    #     print("testing url 7: %s" % github_response_json["token_type"])
    #     print("testing url 8: %s" % github_response_json["scope"])
    #
    #     headers_authorization = {
    #         "Accept": "application/json",
    #         "Authorization": "Bearer %s" % github_response_json["access_token"]
    #     }
    #     authorization_url = DevelopmentConfig.GITHUB_USER
    #
    #     authorization_response = requests.get(
    #         authorization_url,
    #         headers=headers_authorization
    #     )
    #     print("final?")
    #     print(authorization_response)
    #     print(authorization_response.json())
    #
    #     github_user = authorization_response.json()
    #
    #     users_name = github_user["login"]
    #     users_email = github_user["email"]
    #     picture = github_user["avatar_url"]
    #     print("user verified!")
    #     print(users_email)
    #     print(picture)
    #     print(users_name)
    #
    #     login_user_origin(users_name, users_email, 2)
    #
        return redirect("/api/index")
