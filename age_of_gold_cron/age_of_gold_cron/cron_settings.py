from pydantic_settings import BaseSettings, SettingsConfigDict


class CronSettings(BaseSettings):
    POSTGRES_URL: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def ASYNC_DB_URL(self) -> str:
        return "postgresql+asyncpg://{user}:{pw}@{url}:{port}/{db}".format(
            user=self.POSTGRES_USER,
            pw=self.POSTGRES_PASSWORD,
            url=self.POSTGRES_URL,
            port=self.POSTGRES_PORT,
            db=self.POSTGRES_DB,
        )

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = POOL_SIZE * 4
    POOL_RECYCLE: int = 3600
    POOL_PRE_PING: bool = True

    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file="age_of_gold_cron/.env", env_file_encoding="utf-8"
    )


cron_settings = CronSettings()  # type: ignore[call-arg]
