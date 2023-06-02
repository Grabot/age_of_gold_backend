import base64

from flask import render_template

from app_old.routes.forms import EditProfileForm, EmptyForm, LoginForm, RegistrationForm
from app_old.routes.logins.github_login import github_login
from app_old.routes.logins.google_login import google_login
from app_old.routes.logins.reddit_login import reddit_login


def set_routes(app):
    google_login(app)
    github_login(app)
    reddit_login(app)

    @app.route("/api/avatar/<filename>")
    def image_as_html(filename):
        with open("/app_old/static/uploads/%s" % filename, "rb") as fd:
            image_as_base64_html = (
                f"""data:image/png;base64,{base64.encodebytes(fd.read()).decode()}"""
            )

        return render_template("avatar.html", image=image_as_base64_html)
