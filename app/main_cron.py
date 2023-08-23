import asyncio
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlmodel import delete

from app.config.config import settings
from app.models import UserToken

engine_sync = create_engine(settings.SYNC_DB_URL, pool_pre_ping=True, pool_size=32, max_overflow=64)


def remove_expired_tokens():
    print("removing expired tokens")
    with Session(engine_sync) as session:
        delete_expired_tokens = delete(UserToken).where(
            UserToken.refresh_token_expiration < int(time.time())
        )
        session.execute(delete_expired_tokens)
        session.commit()
        print("expired tokens removed")


# We create a separate cron worker for this because if we add the scheduler in the fastapi app,
# it will create multiple cron jobs if we have multiple instances running.
if __name__ == "__main__":
    scheduler = AsyncIOScheduler()
    job = scheduler.add_job(remove_expired_tokens, trigger="cron", hour="0", minute="0")
    scheduler.start()

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
