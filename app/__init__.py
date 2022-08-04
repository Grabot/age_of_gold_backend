from app.config import DevelopmentConfig
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from redis import Redis


db = SQLAlchemy()
migrate = Migrate()
socks = SocketIO(cors_allowed_origins="*")
r = Redis(host=DevelopmentConfig.REDIS_URL, port=DevelopmentConfig.REDIS_PORT)


def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    db.init_app(app)
    socks.init_app(app)
    migrate.init_app(app, db)
    from app.rest import app_api as api_bp
    app.register_blueprint(api_bp)

    from app.sock import app_sock as sock_bp
    app.register_blueprint(sock_bp)

    from app import models

    return app

