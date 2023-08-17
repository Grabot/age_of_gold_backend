import os
import stat

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.api import api_v1
from app.celery_worker.tasks import task_remove_expired_tokens
from app.config.config import settings
from app.sockets.sockets import sio_app


def remove_expired_tokens():
    task_remove_expired_tokens.delay()


scheduler = AsyncIOScheduler()
job = scheduler.add_job(remove_expired_tokens, trigger="cron", hour="0-23", minute="0-59")
scheduler.start()


app = FastAPI()

add_pagination(app)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter()
api_router.include_router(api_v1.api_router_v1, tags=["api_v1"])


app.include_router(api_router, prefix=settings.API_V1_STR)

app.mount("/", sio_app)


@app.on_event("startup")
def startup_function():
    if not os.path.exists(settings.UPLOAD_FOLDER_AVATARS):
        os.makedirs(settings.UPLOAD_FOLDER_AVATARS)
        os.chmod(settings.UPLOAD_FOLDER_AVATARS, stat.S_IRWXO)
    if not os.path.exists(settings.UPLOAD_FOLDER_CRESTS):
        os.makedirs(settings.UPLOAD_FOLDER_CRESTS)
        os.chmod(settings.UPLOAD_FOLDER_CRESTS, stat.S_IRWXO)


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, host="0.0.0.0", reload=True)
