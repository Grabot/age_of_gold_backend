from app.routes.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm
from app.routes.google_login import google_login
from app.routes.regular_login import regular_login


def set_routes(app):
    regular_login(app)
    google_login(app)

