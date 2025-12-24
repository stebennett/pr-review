"""GitHub OAuth service using httpx-oauth.

This module provides a service class that wraps httpx-oauth's GitHubOAuth2 client
for handling GitHub OAuth authentication flow.
"""

import httpx
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.oauth2 import OAuth2Token

from pr_review_api.config import get_settings


class GitHubOAuthService:
    """Service for GitHub OAuth operations.

    Wraps httpx-oauth's GitHubOAuth2 client to provide:
    - Authorization URL generation
    - Code-to-token exchange
    - User info fetching from GitHub API
    """

    # OAuth scopes required for the application
    SCOPES = ["read:org", "repo", "read:user", "user:email"]

    def __init__(self) -> None:
        """Initialize the GitHub OAuth service with settings."""
        settings = get_settings()
        self.client = GitHubOAuth2(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
        )
        self.redirect_uri = settings.github_redirect_uri

    async def get_authorization_url(self, state: str | None = None) -> str:
        """Generate GitHub authorization URL.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            GitHub OAuth authorization URL.
        """
        return await self.client.get_authorization_url(
            redirect_uri=self.redirect_uri,
            scope=self.SCOPES,
            state=state,
        )

    async def exchange_code_for_token(self, code: str) -> OAuth2Token:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from GitHub callback.

        Returns:
            OAuth2Token containing access_token and token metadata.

        Raises:
            httpx_oauth.oauth2.GetAccessTokenError: If token exchange fails.
        """
        return await self.client.get_access_token(
            code=code,
            redirect_uri=self.redirect_uri,
        )

    async def get_user_info(self, access_token: str) -> dict:
        """Fetch user information from GitHub API.

        Args:
            access_token: GitHub OAuth access token.

        Returns:
            Dictionary containing user profile data including:
            - id: GitHub user ID
            - login: GitHub username
            - email: Primary email (may be None)
            - avatar_url: URL to user's avatar

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_emails(self, access_token: str) -> list[dict]:
        """Fetch user's email addresses from GitHub API.

        Used when the user's primary email is not available in their profile
        (e.g., when email is set to private).

        Args:
            access_token: GitHub OAuth access token.

        Returns:
            List of email dictionaries, each containing:
            - email: Email address
            - primary: Whether this is the primary email
            - verified: Whether the email is verified

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            return response.json()


def get_github_oauth_service() -> GitHubOAuthService:
    """Factory function for dependency injection.

    Returns:
        GitHubOAuthService instance.
    """
    return GitHubOAuthService()
