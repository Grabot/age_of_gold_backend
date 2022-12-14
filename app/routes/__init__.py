from app.routes.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm
from app.routes.logins.github_login import github_login
from app.routes.logins.google_login import google_login
from app.routes.logins.reddit_login import reddit_login


def set_routes(app):
    google_login(app)
    github_login(app)
    reddit_login(app)

