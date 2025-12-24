from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    BASE_URL: str

    REDIS_URL: str
    REDIS_PORT: int

    @property
    def REDIS_URI(self) -> str:
        return "redis://{url}:{port}".format(url=self.REDIS_URL, port=self.REDIS_PORT)

    FRONTEND_URL: str

    SMTP_PASSWORD: str
    SMTP_ACCOUNT: str
    SMTP_USER: str
    SMTP_HOST: str
    SMTP_PORT: str

    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str
    S3_SECURE: bool

    S3_ENCRYPTION_KEY: str

    model_config = SettingsConfigDict(
        env_file="age_of_gold_worker/.env",
        env_file_encoding="utf-8",
    )


worker_settings = WorkerSettings()  # type: ignore[call-arg]
