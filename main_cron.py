import asyncio
import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlmodel import delete

from app.config.config import settings
from app.models import UserToken

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

engine_sync = create_engine(
    settings.SYNC_DB_URL, pool_pre_ping=True, pool_size=32, max_overflow=64
)


def remove_expired_tokens():
    logger.info("Starting to remove expired tokens")
    with Session(engine_sync) as session:
        delete_expired_tokens = delete(UserToken).where(
            UserToken.refresh_token_expiration < int(time.time())
        )
        session.execute(delete_expired_tokens)
        session.commit()
    logger.info("Finished removing expired tokens")


async def main():
    logger.info("Starting the scheduler")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        remove_expired_tokens, trigger="cron", hour="11,12,13,14,15,16,17", minute="50"
    )
    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down the scheduler")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
