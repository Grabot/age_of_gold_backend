import logging
from typing import Optional

from celery import Celery

from src.config.config import settings
from src.util.avatar import generate_avatar
from src.util.mail_util import send_delete_account, send_reset_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
celery_app = Celery("tasks", broker=settings.REDIS_URI, backend="rpc://")


@celery_app.task
def task_initialize() -> dict[str, bool]:
    """Initialization."""
    logger.info("initialize task")
    return {"success": True}


@celery_app.task
def task_generate_avatar(
    avatar_filename: str, user_id: Optional[int]
) -> dict[str, bool]:
    """Generate avatar for a new user."""
    if not user_id:
        return {"success": False}
    generate_avatar(avatar_filename, settings.UPLOAD_FOLDER_AVATARS)

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
