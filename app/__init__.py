from app.config import DevelopmentConfig
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from app.routes import set_routes
from oauthlib.oauth2 import WebApplicationClient
from flask_cors import CORS
from flask_mail import Mail


db = SQLAlchemy()
migrate = Migrate()
allow_origin = "*"
# allow_origin = "http://localhost:34745"
socks = SocketIO(cors_allowed_origins=allow_origin)
mail = Mail()

# OAuth 2 client setup
google_client = WebApplicationClient(DevelopmentConfig.GOOGLE_CLIENT_ID)


def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": allow_origin}})
    app.config.from_object(DevelopmentConfig)
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 0
    app.config['SQLALCHEMY_POOL_SIZE'] = 1000
    app.config['SQLALCHEMY_RECORD_QUERIES'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    socks.init_app(app, message_queue=DevelopmentConfig.REDIS_URL)
    migrate.init_app(app, db)
    mail.init_app(app)

    from app.rest import app_api as api_bp
    app.register_blueprint(api_bp)

    from app.sock import app_sock as sock_bp
    app.register_blueprint(sock_bp)

    # Didn't know a better way to do it.
    set_routes(app)

    from app import models

    return app

