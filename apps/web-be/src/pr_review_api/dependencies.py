"""Shared FastAPI dependencies.

This module provides common dependencies used across API endpoints,
including database session injection and authentication helpers.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from pr_review_api.database import get_db
from pr_review_api.models.user import User
from pr_review_api.services.jwt import TokenError, verify_token

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user from the JWT token.

    Extracts the JWT from the Authorization header, validates it,
    and returns the corresponding User from the database.

    Args:
        credentials: HTTP Bearer credentials from the Authorization header.
        db: Database session.

    Returns:
        User instance for the authenticated user.

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found.
    """
    token = credentials.credentials

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


__all__ = ["get_db", "get_current_user"]
