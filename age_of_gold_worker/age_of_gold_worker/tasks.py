from io import BytesIO
from typing import Optional
import logging
from celery import Celery
from age_of_gold_worker.age_of_gold_worker.util import util
from age_of_gold_worker.age_of_gold_worker.worker_settings import worker_settings
from age_of_gold_worker.age_of_gold_worker.util.mail_util import (
    send_reset_email,
    send_delete_account,
)
from .util import avatar
from PIL import Image


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

celery_app = Celery("tasks", broker=worker_settings.REDIS_URI, backend="rpc://")


@celery_app.task
def task_generate_avatar(
    avatar_filename: str,
    s3_key: str,
    user_id: Optional[int],
) -> dict[str, bool]:
    """Generate avatar for a new user."""
    if not user_id:
        return {"success": False}

    avatar_image: Image.Image | None = avatar.generate_avatar(avatar_filename)
    if not avatar_image:
        return {"success": False}

    buffer = BytesIO()
    avatar_image.save(buffer, format="PNG")
    processed_bytes = buffer.getvalue()
    util.worker_upload_image(processed_bytes, worker_settings.S3_BUCKET_NAME, s3_key)

    return {"success": True}


@celery_app.task
def task_send_email_forgot_password(
    to_email: str, subject: str, access_token: str
) -> dict[str, bool]:
    """Send email to reset password."""
    send_reset_email(to_email, subject, access_token)
    return {"success": True}


@celery_app.task
def task_send_email_delete_account(
    to_email: str, subject: str, access_token: str
) -> dict[str, bool]:
    """Send email to reset password."""
    send_delete_account(to_email, subject, access_token)
    return {"success": True}
