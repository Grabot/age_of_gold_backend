"""File for the api router"""

# ruff: noqa: E402
from fastapi import APIRouter

api_router_v1 = APIRouter()

from . import authorization, initialization  # pylint: disable=C0413

__all__ = ["authorization", "initialization"]
