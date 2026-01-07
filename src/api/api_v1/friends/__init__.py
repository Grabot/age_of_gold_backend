"""File for the friend endpoints."""

from . import (
    search_friend,
    add_friend,
    fetch_all_friends,
    respond_friend_request,
    cancel_friend_request,
    remove_friend,
)

__all__ = [
    "add_friend",
    "search_friend",
    "fetch_all_friends",
    "respond_friend_request",
    "cancel_friend_request",
    "remove_friend",
]
