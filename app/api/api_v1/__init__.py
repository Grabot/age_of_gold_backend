# ruff: noqa: E402, F401
from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import authorization, initialization
