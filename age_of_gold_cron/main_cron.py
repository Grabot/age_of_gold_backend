import asyncio
import logging
import time

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
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                delete(UserToken).where(  # type: ignore[arg-type]
                    UserToken.refresh_token_expiration < int(time.time())
                )
            )
    logger.info("Finished removing expired tokens")


if __name__ == "__main__":
    asyncio.run(remove_expired_tokens())
