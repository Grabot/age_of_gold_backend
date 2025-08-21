from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import initialization  # noqa: E402, F401
