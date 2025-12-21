"""
Initialization endpoint for setting up necessary folders and permissions.
"""

import os
import stat

from age_of_gold_worker.age_of_gold_worker import task_initialize
from src.api.api_v1.router import api_router_v1
from src.config.config import settings


@api_router_v1.get("/initialize", status_code=200)
async def initialize_folders() -> dict[str, bool]:
    """
    endpoint for creating folders for storing avatars and crests.
    """
    if not os.path.exists(settings.UPLOAD_FOLDER_AVATARS):
        os.makedirs(settings.UPLOAD_FOLDER_AVATARS)
        os.chmod(
            settings.UPLOAD_FOLDER_AVATARS, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        )
    if not os.path.exists(settings.UPLOAD_FOLDER_CRESTS):
        os.makedirs(settings.UPLOAD_FOLDER_CRESTS)
        os.chmod(
            settings.UPLOAD_FOLDER_CRESTS, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        )

    _ = task_initialize.delay()

    return {"success": True}
