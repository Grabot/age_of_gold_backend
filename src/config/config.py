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

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URL: str
    GOOGLE_DISCOVERY_URL: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    GOOGLE_ACCOUNTS_URL: str = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_ACCESS_TOKEN_URL: str = "https://www.googleapis.com/oauth2/v3/userinfo"
    GOOGLE_AUTHORIZE: str = "https://oauth2.googleapis.com/token"

    GITHUB_AUTHORIZE: str = "https://github.com/login/oauth/authorize"
    GITHUB_ACCESS: str = "https://github.com/login/oauth/access_token"
    GITHUB_USER: str = "https://api.github.com/user"
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URL: str

    REDDIT_AUTHORIZE: str = "https://www.reddit.com/api/v1/authorize"
    REDDIT_ACCESS: str = "https://www.reddit.com/api/v1/access_token"
    REDDIT_USER: str = "https://oauth.reddit.com/api/v1/me"
    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_REDIRECT_URL: str

    APPLE_AUTHORIZE_TOKEN: str = "https://appleid.apple.com/auth/token"
    APPLE_AUTHORIZE: str = "https://appleid.apple.com/auth/authorize"
    APPLE_CLIENT_ID: str
    APPLE_AUD_URL: str = "https://appleid.apple.com"
    APPLE_KEY_ID: str
    APPLE_TEAM_ID: str
    APPLE_AUTH_KEY: str
    APPLE_GRANT_TYPE: str = "authorization_code"
    APPLE_REDIRECT_URL: str

    OAUTH_LIFETIME: int = 600

    JWT_PEM: str
    jwt_alg: str
    jwt_kid: str
    jwt_typ: str
    PRIVATE_KEY_PASSPHRASE: str

    @property
    def header(self) -> Dict[str, str]:
        return {
            "alg": self.jwt_alg,
            "kid": self.jwt_kid,
            "typ": self.jwt_typ,
        }

    JWT_ISS: str
    JWT_AUD: str
    API_SOCK_NAMESPACE: str = "/api/v1.0/sock"

    MAIL_API_KEY: str

    UPLOAD_FOLDER_AVATARS: str = "/src/static/uploads/avatars"
    UPLOAD_FOLDER_CRESTS: str = "/src/static/uploads/crests"
    SHARED_DIR: str

    PEPPER: str

    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = POOL_SIZE * 4
    POOL_RECYCLE: int = 3600
    POOL_PRE_PING: bool = True

    DEBUG: bool = False

    FRONTEND_URL: str
    ALLOWED_ORIGINS: str

    @property
    def ALLOWED_ORIGINS_LIST(self) -> list[str]:
        return self.ALLOWED_ORIGINS.split(",")

    SENDER_MAIL: str
    SENDER_NAME: str = "Age of Gold"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore[call-arg]
