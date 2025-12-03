import asyncio
import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import delete

from src.database import async_session
from src.models.user_token import UserToken

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def remove_expired_tokens() -> None:
    logger.info("Starting to remove expired tokens")
    # TODO: Test this in some way?
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                delete(UserToken).where(  # type: ignore[arg-type]
                    UserToken.refresh_token_expiration < int(time.time())
                )
            )
    logger.info("Finished removing expired tokens")


async def main() -> None:
    logger.info("Starting the scheduler")
    # TODO: Test the scheduler?
    scheduler = AsyncIOScheduler()
    scheduler.add_job(remove_expired_tokens, trigger="cron", hour="0", minute="0")
    scheduler.start()
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down the scheduler")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
