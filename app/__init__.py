from app.config import DevelopmentConfig
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO


db = SQLAlchemy()
migrate = Migrate()
socks = SocketIO(cors_allowed_origins="*")


def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 0
    app.config['SQLALCHEMY_POOL_SIZE'] = 1000
    app.config['SQLALCHEMY_RECORD_QUERIES'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    socks.init_app(app, message_queue=DevelopmentConfig.REDIS_URL)
    migrate.init_app(app, db)
    from app.rest import app_api as api_bp
    app.register_blueprint(api_bp)

    from app.sock import app_sock as sock_bp
    app.register_blueprint(sock_bp)

    from app import models

    return app

