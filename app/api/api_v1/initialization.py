import os
import stat

from app.api.api_v1 import api_router_v1
from app.config.config import settings
from app.celery_worker.tasks import task_initialize


@api_router_v1.get("/initialize", status_code=200)
async def initialize_folders() -> dict:

    if not os.path.exists(settings.UPLOAD_FOLDER_AVATARS):
        os.makedirs(settings.UPLOAD_FOLDER_AVATARS)
        os.chmod(settings.UPLOAD_FOLDER_AVATARS, stat.S_IRWXO)
    if not os.path.exists(settings.UPLOAD_FOLDER_CRESTS):
        os.makedirs(settings.UPLOAD_FOLDER_CRESTS)
        os.chmod(settings.UPLOAD_FOLDER_CRESTS, stat.S_IRWXO)

    _ = task_initialize.delay()

    return {"results": "true"}
