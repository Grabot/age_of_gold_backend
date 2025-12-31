"""Base file for the api router and endpoints."""

from . import authorization, oauth, settings, friends, user
from .router import api_router_v1

__all__ = ["authorization", "api_router_v1", "oauth", "settings", "user", "friends"]
