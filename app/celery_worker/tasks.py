import logging

from celery import Celery

from app.config.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

celery_app = Celery(
    "tasks", broker=settings.REDIS_URI, backend=f"db+{settings.SYNC_DB_URL}"
)


@celery_app.task
def task_initialize():
    logger.info("initialize task")
    return {"success": True}
