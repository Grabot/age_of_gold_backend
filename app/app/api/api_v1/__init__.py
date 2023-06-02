from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import test, user_access
