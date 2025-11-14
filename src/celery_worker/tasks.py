import logging
from typing import Optional

import httpx
import requests
from celery import Celery

from src.config.config import settings
from src.util.avatar import generate_avatar

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
def task_generate_avatar(
    avatar_filename: str, user_id: Optional[int]
) -> dict[str, bool]:
    print("task generating avatar")
    print(f"avatar_filename: {avatar_filename}")
    print(f"user_id: {user_id}")
    if not user_id:
        print("there was no user id?")
        return {"success": False}
    print("generating avatar")
    generate_avatar(avatar_filename, settings.UPLOAD_FOLDER_AVATARS)
    print("generating avatar done")

    base_url = settings.BASE_URL
    api_prefix = settings.API_V1_STR
    endpoint = "/avatar/created"
    total_url = base_url + api_prefix + endpoint
    print(f"total_url: {total_url}")
    requests.post(total_url, json={"user_id": user_id})
    print("Done")

    return {"success": True}
