from app.config import DevelopmentConfig
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from app.routes import set_routes
from flask_login import LoginManager
from oauthlib.oauth2 import WebApplicationClient
from flask_httpauth import HTTPTokenAuth
from flask_cors import CORS


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
auth = HTTPTokenAuth(scheme='Bearer')
socks = SocketIO(cors_allowed_origins="*")

# OAuth 2 client setup
google_client = WebApplicationClient(DevelopmentConfig.GOOGLE_CLIENT_ID)


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config.from_object(DevelopmentConfig)
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 0
    app.config['SQLALCHEMY_POOL_SIZE'] = 1000
    app.config['SQLALCHEMY_RECORD_QUERIES'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    login.init_app(app)
    login.login_view = 'login'
    socks.init_app(app, message_queue=DevelopmentConfig.REDIS_URL)
    migrate.init_app(app, db)

    from app.rest import app_api as api_bp
    app.register_blueprint(api_bp)

    from app.sock import app_sock as sock_bp
    app.register_blueprint(sock_bp)

    # Didn't know a better way to do it.
    set_routes(app)

    from app import models

    return app

