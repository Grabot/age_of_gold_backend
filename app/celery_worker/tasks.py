import logging

import requests
from celery import Celery

from app.config.config import settings
from app.util.avatar import generate_avatar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

celery_app = Celery("tasks", broker=settings.REDIS_URI, backend="rpc://")


@celery_app.task
def task_initialize() -> dict[str, bool]:
    logger.info("initialize task")
    return {"success": True}


@celery_app.task
def task_generate_avatar(avatar_filename: str, user_id: int) -> dict[str, bool]:
    generate_avatar(avatar_filename, settings.UPLOAD_FOLDER_AVATARS)

    base_url = settings.BASE_URL
    api_prefix = settings.API_V1_STR
    endpoint = "/avatar/created"
    total_url = base_url + api_prefix + endpoint
    requests.post(total_url, json={"user_id": user_id})

    return {"success": True}
