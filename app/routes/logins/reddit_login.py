from flask import redirect, request
import requests
from app.config import DevelopmentConfig
from urllib.parse import urlencode
from base64 import b64encode
from app.routes.login_user_origin import login_user_origin


#TODO: turn it to api endpoints?
def reddit_login(app):

    @app.route("/login/reddit", methods=['GET', 'POST'])
    def login_reddit():
        print("attempting to login reddit :)")
        # TODO: correct endpoint?
        base_url = DevelopmentConfig.REDDIT_AUTHORIZE
        params = dict()
        params["client_id"] = DevelopmentConfig.REDDIT_CLIENT_ID
        params["duration"] = "temporary"
        params["redirect_uri"] = DevelopmentConfig.REDDIT_REDIRECT
        params["response_type"] = "code"
        params["scope"] = "identity"
        params["state"] = "x"

        url_params = urlencode(params)
        reddit_url = base_url + "/?" + url_params
        print("testing url: %s" % reddit_url)

        return redirect(reddit_url)

    @app.route("/login/reddit/callback", methods=['GET', 'POST'])
    def reddit_callback():
        # Get authorization code Google sent back to you
        print("reddit callback!!!!")
        code = request.args.get("code")
        print("code: %s" % code)
        state = request.args.get("state")
        print("state: %s" % state)

        access_base_url = DevelopmentConfig.REDDIT_ACCESS

        print("reddit post url: %s" % access_base_url)

        token_post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DevelopmentConfig.REDDIT_REDIRECT
        }

        encoded_authorization = "%s:%s" % (DevelopmentConfig.REDDIT_CLIENT_ID, DevelopmentConfig.REDDIT_CLIENT_SECRET)

        http_auth = b64encode(encoded_authorization.encode("utf-8")).decode("utf-8")
        authorization = "Basic %s" % http_auth
        print("authorization: %s" % authorization)
        headers = {
            "Accept": "application/json",
            'User-agent': 'age of gold login bot 0.1',
            "Authorization": authorization
        }

        print("url: %s" % access_base_url)
        print("headers: %s" % headers)
        print("data: %s" % token_post_data)
        token_response = requests.post(
            access_base_url,
            headers=headers,
            data=token_post_data
        )

        print("testing url 2: %s" % token_response)
        print("testing url 3: %s" % token_response.url)

        print("testing url 3: %s" % token_response.text)
        print("testing url 4: %s" % token_response.json())
        reddit_response_json = token_response.json()
        print("testing url 5: %s" % reddit_response_json)
        print("testing url 6: %s" % reddit_response_json["access_token"])
        print("testing url 7: %s" % reddit_response_json["token_type"])
        print("testing url 8: %s" % reddit_response_json["scope"])
        print("testing url 8: %s" % reddit_response_json["expires_in"])

        headers_authorization = {
            "Accept": "application/json",
            'User-agent': 'age of gold login bot 0.1',
            "Authorization": "bearer %s" % reddit_response_json["access_token"]
        }
        # authorization_url = DevelopmentConfig.REDDIT_USER
        authorization_url = "https://oauth.reddit.com/api/v1/me"

        authorization_response = requests.get(
            authorization_url,
            headers=headers_authorization
        )
        print("final?")
        print(authorization_response)
        print(authorization_response.json())

        reddit_user = authorization_response.json()

        users_name = reddit_user["name"]
        users_email = "reddit"  # Reddit gives no email?
        picture = reddit_user["icon_img"]

        login_user_origin(users_name, users_email, 2)

        params = dict()
        params["access_token"] = "test"
        params["refresh_token"] = "test2"
        url_params = urlencode(params)

        # Send user to the world
        world_url = request.base_url.replace("/login/reddit/callback", "/worldaccess")
        world_url_params = world_url + "?" + url_params
        # Send user to the world
        return redirect(world_url_params)
