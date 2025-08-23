from fastapi import APIRouter, FastAPI
from fastapi_pagination import add_pagination

from app.api import api_v1
from app.config.config import settings

app_test = FastAPI()

add_pagination(app_test)

api_router = APIRouter()
api_router.include_router(api_v1.api_router_v1, tags=["api_v1"])


app_test.include_router(api_router, prefix=settings.API_V1_STR)
