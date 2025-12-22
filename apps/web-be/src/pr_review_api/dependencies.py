"""Shared FastAPI dependencies.

This module provides common dependencies used across API endpoints,
including database session injection and authentication helpers.
"""

from pr_review_api.database import get_db

# Re-export get_db for convenience
__all__ = ["get_db"]
