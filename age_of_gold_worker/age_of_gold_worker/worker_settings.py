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

    UPLOAD_FOLDER_AVATARS: str = "/src/static/uploads/avatars"
    UPLOAD_FOLDER_CRESTS: str = "/src/static/uploads/crests"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


worker_settings = WorkerSettings()  # type: ignore[call-arg]
