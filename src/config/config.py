from typing import Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_URL: str

    API_V1_STR: str = "/api/v1.0"

    POSTGRES_URL: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    REDIS_URL: str
    REDIS_PORT: int

    @property
    def ASYNC_DB_URL(self) -> str:
        return "postgresql+asyncpg://{user}:{pw}@{url}:{port}/{db}".format(
            user=self.POSTGRES_USER,
            pw=self.POSTGRES_PASSWORD,
            url=self.POSTGRES_URL,
            port=self.POSTGRES_PORT,
            db=self.POSTGRES_DB,
        )

    @property
    def REDIS_URI(self) -> str:
        return "redis://{url}:{port}".format(url=self.REDIS_URL, port=self.REDIS_PORT)

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SECRET_KEY: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_DISCOVERY_URL: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    GOOGLE_ACCESS_TOKEN_URL: str = "https://www.googleapis.com/oauth2/v3/userinfo"

    GITHUB_AUTHORIZE: str = "https://github.com/login/oauth/authorize"
    GITHUB_ACCESS: str = "https://github.com/login/oauth/access_token"
    GITHUB_USER: str = "https://api.github.com/user"
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    REDDIT_AUTHORIZE: str = "https://www.reddit.com/api/v1/authorize"
    REDDIT_ACCESS: str = "https://www.reddit.com/api/v1/access_token"
    REDDIT_USER: str = "https://oauth.reddit.com/api/v1/me"
    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_REDIRECT: str = "https://ageof.gold/login/reddit/callback"

    APPLE_AUTHORIZE: str = "https://appleid.apple.com/auth/token"
    APPLE_CLIENT_ID: str
    APPLE_AUD_URL: str = "https://appleid.apple.com"
    APPLE_KEY_ID: str
    APPLE_TEAM_ID: str
    APPLE_AUTH_KEY: str
    APPLE_GRANT_TYPE: str = "authorization_code"
    APPLE_REDIRECT_URL: str

    PACKAGE_NAME: str = "ageof.gold.age_of_gold"

    jwt_pem: str
    jwt_alg: str
    jwt_kid: str
    jwt_typ: str

    @property
    def header(self) -> Dict[str, str]:
        return {
            "alg": self.jwt_alg,
            "kid": self.jwt_kid,
            "typ": self.jwt_typ,
        }

    JWT_SUB: str
    JWT_ISS: str
    JWT_AUD: str
    API_SOCK_NAMESPACE: str = "/api/v1.0/sock"

    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USE_TLS: bool
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SENDERNAME: str
    UPLOAD_FOLDER_AVATARS: str = "/app/static/uploads/avatars"
    UPLOAD_FOLDER_CRESTS: str = "/app/static/uploads/crests"

    PEPPER: str

    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = POOL_SIZE * 4
    POOL_RECYCLE: int = 3600
    POOL_PRE_PING: bool = True

    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
