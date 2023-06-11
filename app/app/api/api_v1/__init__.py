from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import email, map, message, test, user_access
