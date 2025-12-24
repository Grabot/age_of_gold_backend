from contextlib import asynccontextmanager
from typing import AsyncGenerator

import boto3
import uvicorn
from botocore import client as boto_client
from cryptography.fernet import Fernet
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from src.api import api_v1
from src.config.config import settings
from src.sockets.sockets import sio_app
from src.util.gold_logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
    cipher = Fernet(settings.S3_ENCRYPTION_KEY.encode())
    app.state.cipher = cipher
    app.state.s3 = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="eu-central-1",
        config=boto_client.Config(signature_version="s3v4"),
    )
    try:
        logger.info("bucket")
        app.state.s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except Exception:
        logger.info("CREATE!")
        app.state.s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)

    yield


app = FastAPI(lifespan=lifespan)

add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter()
api_router.include_router(api_v1.api_router_v1, tags=["api_v1"])

app.include_router(api_router, prefix=settings.API_V1_STR)

app.mount("/", sio_app)

if __name__ == "__main__":  # pragma: no cover
    logger.info("Starting the backend")
    uvicorn.run(
        "main:app",
        port=5000,
        host="0.0.0.0",
        reload=True,
    )
