import requests
from celery import Celery

from app.config.config import settings
from app.util.avatar.generate_avatar import generate_avatar

celery_app = Celery("tasks", broker=settings.REDIS_URI, backend=f"db+{settings.SYNC_DB_URL}")


@celery_app.task
def task_generate_avatar(avatar_filename: str, user_id: int):
    print("going to generate avatar")
    generate_avatar(avatar_filename, settings.UPLOAD_FOLDER)

    base_url = settings.BASE_URL
    api_prefix = settings.API_V1_STR
    endpoint = "/avatar/created"
    total_url = base_url + api_prefix + endpoint
    print(f"url {total_url}")
    get_result = requests.post(total_url, json={"user_id": user_id})
    print(f"getting result {get_result}")

    return {"success": True}
