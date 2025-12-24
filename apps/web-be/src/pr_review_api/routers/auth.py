"""Authentication router for GitHub OAuth flow.

This module provides endpoints for:
- Initiating GitHub OAuth login
- Handling OAuth callback
- Getting current user info
- Logging out
"""

import secrets

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from pr_review_shared import encrypt_token
from sqlalchemy.orm import Session

from pr_review_api.config import Settings, get_settings
from pr_review_api.database import get_db
from pr_review_api.dependencies import get_current_user
from pr_review_api.models.user import User
from pr_review_api.schemas.auth import LoginResponse, UserResponse
from pr_review_api.services.github import GitHubOAuthService, get_github_oauth_service
from pr_review_api.services.jwt import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/login", response_model=LoginResponse)
async def login(
    github_service: GitHubOAuthService = Depends(get_github_oauth_service),
) -> LoginResponse:
    """Initiate GitHub OAuth flow.

    Returns the GitHub authorization URL that the client should redirect to.
    The URL includes the required scopes for reading organizations and repositories.

    Returns:
        LoginResponse with the GitHub OAuth authorization URL.
    """
    # Generate state parameter for CSRF protection
    # Note: For production, state should be stored (session/cache) and validated in callback
    state = secrets.token_urlsafe(32)

    authorization_url = await github_service.get_authorization_url(state=state)
    return LoginResponse(url=authorization_url)


@router.get("/callback")
async def callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(None, description="State parameter for CSRF validation"),
    github_service: GitHubOAuthService = Depends(get_github_oauth_service),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Handle GitHub OAuth callback.

    Exchanges the authorization code for an access token, fetches user info,
    creates/updates the user in the database, and redirects to the frontend
    with a JWT token.

    Args:
        code: Authorization code from GitHub.
        state: State parameter for CSRF validation (not validated in MVP).
        github_service: GitHub OAuth service.
        db: Database session.
        settings: Application settings.

    Returns:
        RedirectResponse to frontend with JWT token or error.
    """
    frontend_url = settings.frontend_url

    try:
        # Exchange code for access token
        token_data = await github_service.exchange_code_for_token(code)
        access_token = token_data["access_token"]

        # Fetch user info from GitHub
        user_info = await github_service.get_user_info(access_token)

        # Try to get primary email if not in profile
        email = user_info.get("email")
        if not email:
            try:
                emails = await github_service.get_user_emails(access_token)
                primary_email = next(
                    (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                    None,
                )
                email = primary_email
            except Exception:
                # Email fetch failed, continue without email
                pass

        # Encrypt the access token for storage
        github_user_id = str(user_info["id"])
        encrypted_token = encrypt_token(access_token, settings.encryption_key)

        # Create or update user in database
        user = db.query(User).filter(User.id == github_user_id).first()
        if user:
            # Update existing user
            user.github_username = user_info["login"]
            user.github_access_token = encrypted_token
            if email:
                user.email = email
            user.avatar_url = user_info.get("avatar_url")
        else:
            # Create new user
            user = User(
                id=github_user_id,
                github_username=user_info["login"],
                github_access_token=encrypted_token,
                email=email,
                avatar_url=user_info.get("avatar_url"),
            )
            db.add(user)

        db.commit()

        # Generate JWT token
        jwt_token = create_access_token(user_id=github_user_id)

        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{frontend_url}?token={jwt_token}",
            status_code=302,
        )

    except Exception:
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed",
            status_code=302,
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get the current authenticated user's information.

    Requires a valid JWT token in the Authorization header.

    Args:
        current_user: Current authenticated user from JWT.

    Returns:
        UserResponse with user information.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.github_username,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
    )


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout the current user.

    This is a client-side operation - the client should discard the JWT token.
    The endpoint exists for API completeness and potential audit logging.

    Returns:
        Success message.
    """
    return {"message": "Successfully logged out"}
