import os
import stat

from app.api.api_v1 import api_router_v1
from app.celery_worker.tasks import task_initialize
from app.config.config import settings


@api_router_v1.get("/initialize", status_code=200)
async def initialize_folders() -> dict[str, str]:
    if not os.path.exists(settings.UPLOAD_FOLDER_AVATARS):
        os.makedirs(settings.UPLOAD_FOLDER_AVATARS)
        os.chmod(settings.UPLOAD_FOLDER_AVATARS, stat.S_IRWXO)
    if not os.path.exists(settings.UPLOAD_FOLDER_CRESTS):
        os.makedirs(settings.UPLOAD_FOLDER_CRESTS)
        os.chmod(settings.UPLOAD_FOLDER_CRESTS, stat.S_IRWXO)

    _ = task_initialize.delay()

    return {"results": "true"}
