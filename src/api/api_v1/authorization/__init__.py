"""File for the authorization endpoints"""

from . import login, logout, register, token_login, token_refresh

__all__ = ["login", "logout", "token_refresh", "register", "token_login"]
