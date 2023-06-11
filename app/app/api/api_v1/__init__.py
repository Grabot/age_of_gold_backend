from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import email, map, message, settings, test, user_access
