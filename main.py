import logging

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.api import api_v1
from app.config.config import settings
from app.sockets.sockets import sio_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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


if __name__ == "__main__":
    logger.info("Starting the backend")
    uvicorn.run("main:app", port=5000, host="0.0.0.0", reload=True)
