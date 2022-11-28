from flask import redirect, request
from flask_login import current_user
import requests
from app.config import DevelopmentConfig
import json
from app.routes.login_user_origin import login_user_origin
from urllib.parse import urlencode


def get_google_provider_cfg():
    return requests.get(DevelopmentConfig.GOOGLE_DISCOVERY_URL).json()


# TODO: turn it to api endpoints?
def google_login(app):

    from app import google_client

    @app.route("/login/google", methods=['GET', 'POST'])
    def login_google():
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()

        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        final_redirect_url = request.base_url.replace("http://", "https://", 1)
        print("redirect uri: %s" % final_redirect_url)
        request_uri = google_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=final_redirect_url + "/callback",
            scope=["openid", "email", "profile"],
        )
        print("request_uri: %s" % request_uri)
        print("url: %s" % request.url)
        return redirect(request_uri)

    @app.route("/login/google/callback", methods=['GET', 'POST'])
    def google_callback():
        # Get authorization code Google sent back to you
        code = request.args.get("code")
        print("code: %s" % code)

        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay, tokens!
        # Not sure why it reverts to regular http:// but change it back to secure connection
        final_redirect_url = request.base_url.replace("http://", "https://", 1)
        print("final_authorization_response: %s" % final_redirect_url)
        authorization_response = request.url.replace("http://", "https://", 1)
        print("request url: %s" % request.url)
        token_url, headers, body = google_client.prepare_token_request(
            token_endpoint,
            authorization_response=authorization_response,
            redirect_url=final_redirect_url,
            code=code
        )
        print("token_url: %s" % token_url)
        print("headers: %s" % headers)
        print("body: %s" % body)
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(DevelopmentConfig.GOOGLE_CLIENT_ID, DevelopmentConfig.GOOGLE_CLIENT_SECRET),
        )
        print("response? :% s" % token_response)
        # Parse the tokens!
        google_client.parse_request_body_response(json.dumps(token_response.json()))

        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = google_client.add_token(userinfo_endpoint)
        print("uri: %s" % uri)
        print("headers: %s" % headers)
        print("body: %s" % body)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # You want to make sure their email is verified.
        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        if not userinfo_response.json().get("email_verified"):
            return "User email not available or not verified by Google.", 400

        print("complete_json: %s" % userinfo_response.json())
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        print("user verified!")
        print(users_email)
        print(picture)
        print(users_name)

        login_user_origin(users_name, users_email, 1)
        # TODO: Create tokens for user? (both very low life?)
        params = dict()
        params["access_token"] = "test"
        params["refresh_token"] = "test2"
        url_params = urlencode(params)

        # Send user to the world
        world_url = request.base_url.replace("/login/google/callback", "/worldaccess")
        world_url_params = world_url + "?" + url_params
        print("redirected to the url: %s" % world_url_params)
        return redirect(world_url_params)

