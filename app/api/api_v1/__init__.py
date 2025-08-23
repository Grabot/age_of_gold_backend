# ruff: noqa: E402
from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import authorization, initialization

__all__ = ["authorization", "initialization"]
