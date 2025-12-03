"""File for the oauth endpoints."""

from . import apple_oauth, github_oauth, google_oauth, reddit_oauth

__all__ = ["google_oauth", "github_oauth", "reddit_oauth", "apple_oauth"]
