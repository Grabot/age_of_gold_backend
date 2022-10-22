from flask import redirect, request
from flask_login import current_user, login_user
import requests
from app.config import DevelopmentConfig
import json


def get_google_provider_cfg():
    return requests.get(DevelopmentConfig.GOOGLE_DISCOVERY_URL).json()


def google_login(app):

    @app.route("/google/test", methods=['GET', 'POST'])
    def google_test():
        if current_user.is_authenticated:
            return (
                "<p>Hello, {}! You're logged in! Email: {}</p>"
                "<div><p>Google Profile Picture:</p>"
                '<img src="{}" alt="Google profile pic"></img></div>'
                '<a class="button" href="/logout">Logout</a>'.format(
                    current_user.name, current_user.email, current_user.profile_pic
                )
            )
        else:
            return '<a class="button" href="/google/test/login">Google Login</a>'

    from app import google_client

    @app.route("/google/test/login", methods=['GET', 'POST'])
    def login_google():
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        if request.scheme == "http":
            print("http")
            request.scheme = "https"
        if request.scheme == "https":
            print("HTTPS!")
        print("request: %s" % request.base_url)
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        final_redirect_url = request.base_url.replace("http://", "https://")
        request_uri = google_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=final_redirect_url + "/callback",
            scope=["openid", "email", "profile"],
        )
        print("request_uri: %s" % request_uri)
        print("url: %s" % request.url)
        return redirect(request_uri)

    from app import db
    from app.models.user import User

    @app.route("/google/test/login/callback", methods=['GET', 'POST'])
    def callback():
        # Get authorization code Google sent back to you
        code = request.args.get("code")
        print("code: %s" % code)

        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        # Not sure why it reverts to regular http:// but change it back to secure connection
        final_redirect_url = request.base_url.replace("http://", "https://")
        print("final_authorization_response: %s" % final_redirect_url)
        print("request url: %s" % request.url)
        token_url, headers, body = google_client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
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
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # You want to make sure their email is verified.
        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        if not userinfo_response.json().get("email_verified"):
            return "User email not available or not verified by Google.", 400

        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        print("user verified!")
        print(unique_id)
        print(users_email)
        print(picture)
        print(users_name)
        # Check if the user has logged in before using google.
        # If that's the case it has a Row in the database, and we log in
        # (we don't use the username, because the user can change it from the Google name)
        google_user = User.query.filter_by(email=users_email, origin=1).first()
        if google_user is None:
            print("new user")
            # If not than we create a new entry in the database and then log in.
            # The last verification is to check if username is not taken
            new_user = User.query.filter_by(username=users_name).first()
            if new_user is None:
                print("really new user!")
                user = User(
                    username=users_name,
                    email=users_email,
                    password_hash="",
                    origin=1
                )
                db.session.add(user)
                db.session.commit()
                login_user(user)
            else:
                print("username is taken....")
                # If the username is taken than we change it because we have to create the user here.
                # The user can change it later if he really hates it.
                index = 2
                while index < 100:
                    new_user_name = users_name + "_%s" % index
                    print("attempting user creation with username: %s" % new_user_name)
                    new_user = User.query.filter_by(username=new_user_name).first()
                    if new_user is None:
                        print("we finally have a correct username!")
                        user = User(
                            username=new_user_name,
                            email=users_email,
                            password_hash="",
                            origin=1
                        )
                        db.session.add(user)
                        db.session.commit()
                        login_user(user)
                        break
                    else:
                        print("still taken...")
                        index += 1
                return "User creation failed, sorry", 400
        else:
            print("logging in existing user")
            login_user(google_user)

        # Send user back to homepage
        return redirect("/index")

