import os
from typing import Dict, List, Optional, Union

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_URL: str = os.environ.get("BASE_URL", "")

    API_V1_STR: str = "/api/v1.0"

    POSTGRES_URL: str = os.environ.get("POSTGRES_URL", "")
    POSTGRES_PORT: int = int(os.environ.get("POSTGRES_PORT", 5432))
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "")

    REDIS_URL: str = os.environ.get("REDIS_URL", "")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", 6379))

    ASYNC_DB_URL: str = "postgresql+asyncpg://{user}:{pw}@{url}:{port}/{db}".format(
        user=POSTGRES_USER,
        pw=POSTGRES_PASSWORD,
        url=POSTGRES_URL,
        port=POSTGRES_PORT,
        db=POSTGRES_DB,
    )

    SYNC_DB_URL: str = "postgresql://{user}:{pw}@{url}:{port}/{db}".format(
        user=POSTGRES_USER,
        pw=POSTGRES_PASSWORD,
        url=POSTGRES_URL,
        port=POSTGRES_PORT,
        db=POSTGRES_DB,
    )

    REDIS_URI: str = "redis://{url}:{port}".format(url=REDIS_URL, port=REDIS_PORT)

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "you-will-never-guess")

    GOOGLE_CLIENT_ID: Optional[str] = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET: Optional[str] = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    GOOGLE_ACCESS_TOKEN_URL: str = "https://www.googleapis.com/oauth2/v3/userinfo"

    GITHUB_AUTHORIZE: str = "https://github.com/login/oauth/authorize"
    GITHUB_ACCESS: str = "https://github.com/login/oauth/access_token"
    GITHUB_USER: str = "https://api.github.com/user"
    GITHUB_CLIENT_ID: Optional[str] = os.environ.get("GITHUB_CLIENT_ID", None)
    GITHUB_CLIENT_SECRET: Optional[str] = os.environ.get("GITHUB_CLIENT_SECRET", None)

    REDDIT_AUTHORIZE: str = "https://www.reddit.com/api/v1/authorize"
    REDDIT_ACCESS: str = "https://www.reddit.com/api/v1/access_token"
    REDDIT_USER: str = "https://oauth.reddit.com/api/v1/me"
    REDDIT_CLIENT_ID: Optional[str] = os.environ.get("REDDIT_CLIENT_ID", None)
    REDDIT_CLIENT_SECRET: Optional[str] = os.environ.get("REDDIT_CLIENT_SECRET", None)
    REDDIT_REDIRECT: str = "https://ageof.gold/login/reddit/callback"

    APPLE_AUTHORIZE: str = "https://appleid.apple.com/auth/token"
    APPLE_CLIENT_ID: Optional[str] = os.environ.get("APPLE_CLIENT_ID", None)
    APPLE_AUD_URL: str = "https://appleid.apple.com"
    APPLE_KEY_ID: Optional[str] = os.environ.get("APPLE_KEY_ID", None)
    APPLE_TEAM_ID: Optional[str] = os.environ.get("APPLE_TEAM_ID", None)
    APPLE_AUTH_KEY: Optional[str] = os.environ.get("APPLE_AUTH_KEY", None)
    APPLE_GRANT_TYPE: str = "authorization_code"
    APPLE_REDIRECT_URL: Optional[str] = os.environ.get("APPLE_REDIRECT_URL", None)

    PACKAGE_NAME: str = "ageof.gold.age_of_gold"

    jwk: Dict[str, Union[str, List[str]]] = {
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

    header: Dict[str, str] = {
        "alg": os.environ.get("JWT_ALG", ""),
        "kid": os.environ.get("JWT_KID", ""),
        "typ": os.environ.get("JWT_TYP", ""),
    }
    map_size: int = 150
    JWT_SUB: str = os.environ.get("JWT_SUB", "")
    JWT_ISS: str = os.environ.get("JWT_ISS", "")
    JWT_AUD: str = os.environ.get("JWT_AUD", "")
    API_SOCK_NAMESPACE: str = "/api/v1.0/sock"

    MAIL_SERVER: Optional[str] = os.environ.get("MAIL_SERVER")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", 25))
    MAIL_USE_TLS: bool = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME: Optional[str] = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD: Optional[str] = os.environ.get("MAIL_PASSWORD")
    MAIL_SENDERNAME: Optional[str] = os.environ.get("MAIL_SENDERNAME")
    UPLOAD_FOLDER_AVATARS: str = "/app/static/uploads/avatars"
    UPLOAD_FOLDER_CRESTS: str = "/app/static/uploads/crests"

    class Config:
        case_sensitive: bool = True


settings = Settings()
