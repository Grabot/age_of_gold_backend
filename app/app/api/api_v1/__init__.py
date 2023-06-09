from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import map, message, test, user_access
