import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1.0"

    POSTGRES_URL = os.environ["POSTGRES_URL"]
    POSTGRES_PORT = os.environ["POSTGRES_PORT"]
    POSTGRES_USER = os.environ["POSTGRES_USER"]
    POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
    POSTGRES_DB = os.environ["POSTGRES_DB"]

    REDIS_URL = os.environ["REDIS_URL"]
    REDIS_PORT = os.environ["REDIS_PORT"]

    PASSWORD_AGE_OF_GOLD = os.environ["PASSWORD_AGE_OF_GOLD"]

    DB_URL = "postgresql+asyncpg://{user}:{pw}@{url}:{port}/{db}".format(
        user=POSTGRES_USER,
        pw=POSTGRES_PASSWORD,
        url=POSTGRES_URL,
        port=POSTGRES_PORT,
        db=POSTGRES_DB,
    )

    REDIS_URI = "redis://{url}:{port}".format(url=REDIS_URL, port=REDIS_PORT)

    SQLALCHEMY_DATABASE_URI = DB_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    # Configuration
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
    GITHUB_ACCESS = "https://github.com/login/oauth/access_token"
    GITHUB_USER = "https://api.github.com/user"
    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", None)
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", None)

    REDDIT_AUTHORIZE = "https://www.reddit.com/api/v1/authorize"
    REDDIT_ACCESS = "https://www.reddit.com/api/v1/access_token"
    REDDIT_USER = "https://oauth.reddit.com/api/v1/me"
    REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", None)
    REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", None)
    REDDIT_REDIRECT = "https://ageof.gold/login/reddit/callback"
    DEBUG = True

    jwk = {
        "alg": os.environ.get("JWT_ALG", ""),
        "crv": os.environ.get("JWT_CRV", ""),
        "d": os.environ.get("JWT_D", ""),
        "key_ops": ["sign", "verify"],
        "kty": os.environ.get("JWT_KTY", ""),
        "x": os.environ.get("JWT_X", ""),
        "y": os.environ.get("JWT_Y", ""),
        "use": os.environ.get("JWT_USE", ""),
        "kid": os.environ.get("JWT_KID", ""),
    }

    header = {
        "alg": os.environ.get("JWT_ALG", ""),
        "kid": os.environ.get("JWT_KID", ""),
        "typ": os.environ.get("JWT_TYP", ""),
    }
    map_size = 50
    JWT_SUB = os.environ.get("JWT_SUB", "")
    JWT_ISS = os.environ.get("JWT_ISS", "")
    JWT_AUD = os.environ.get("JWT_AUD", "")
    API_SOCK_NAMESPACE = "/api/v1.0/sock"

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    BASE_URL = os.environ.get("BASE_URL")
    UPLOAD_FOLDER = "static/uploads/"

    class Config:
        case_sensitive = True


settings = Settings()
