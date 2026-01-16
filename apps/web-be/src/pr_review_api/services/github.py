"""GitHub services for OAuth and API operations.

This module provides service classes for:
- GitHubOAuthService: Handles GitHub OAuth authentication flow
- GitHubAPIService: Fetches data from GitHub API (orgs, repos, PRs)
"""

from datetime import UTC, datetime

import httpx
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.oauth2 import OAuth2Token

from pr_review_api.config import get_settings
from pr_review_api.schemas import (
    Author,
    InaccessibleRepository,
    Label,
    Organization,
    PATValidationResult,
    PullRequest,
    RateLimitInfo,
    Repository,
    RepositoryAccessResult,
    RepositoryRef,
)


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


class GitHubAPIService:
    """Service for GitHub API data fetching operations.

    Provides methods to fetch organizations, repositories, pull requests,
    and check statuses from the GitHub API. All methods track rate limit
    information from response headers.
    """

    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_HEADERS = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    def _get_headers(self, access_token: str) -> dict[str, str]:
        """Build headers for GitHub API requests.

        Args:
            access_token: GitHub OAuth access token or PAT.

        Returns:
            Headers dictionary with authorization and API version.
        """
        return {
            **self.GITHUB_HEADERS,
            "Authorization": f"Bearer {access_token}",
        }

    def _parse_rate_limit(self, response: httpx.Response) -> RateLimitInfo:
        """Parse rate limit information from response headers.

        Args:
            response: HTTP response from GitHub API.

        Returns:
            RateLimitInfo with remaining requests and reset time.
        """
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        reset_timestamp = int(response.headers.get("X-RateLimit-Reset", 0))
        reset_at = datetime.fromtimestamp(reset_timestamp, tz=UTC)
        return RateLimitInfo(remaining=remaining, reset_at=reset_at)

    async def get_user_organizations(
        self, access_token: str
    ) -> tuple[list[Organization], RateLimitInfo]:
        """Fetch organizations the user has access to.

        This includes the user's personal account (for personal repos)
        plus any organizations they are a member of.

        Args:
            access_token: GitHub OAuth access token.

        Returns:
            Tuple of (list of organizations, rate limit info).

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        async with httpx.AsyncClient() as client:
            # First fetch the user's own account info
            user_response = await client.get(
                f"{self.GITHUB_API_BASE}/user",
                headers=self._get_headers(access_token),
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            # Then fetch organizations
            response = await client.get(
                f"{self.GITHUB_API_BASE}/user/orgs",
                headers=self._get_headers(access_token),
            )
            response.raise_for_status()

            rate_limit = self._parse_rate_limit(response)
            orgs_data = response.json()

            # Start with user's personal account
            organizations = [
                Organization(
                    id=str(user_data["id"]),
                    login=user_data["login"],
                    avatar_url=user_data.get("avatar_url"),
                )
            ]

            # Add organizations they belong to
            organizations.extend(
                [
                    Organization(
                        id=str(org["id"]),
                        login=org["login"],
                        avatar_url=org.get("avatar_url"),
                    )
                    for org in orgs_data
                ]
            )

            return organizations, rate_limit

    async def get_organization_repositories(
        self, access_token: str, org: str
    ) -> tuple[list[Repository], RateLimitInfo]:
        """Fetch repositories in an organization or user account.

        For organizations, uses /orgs/{org}/repos endpoint.
        For personal accounts, uses /users/{username}/repos endpoint.

        Args:
            access_token: GitHub OAuth access token.
            org: Organization or user login name.

        Returns:
            Tuple of (list of repositories, rate limit info).

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        async with httpx.AsyncClient() as client:
            # Try organization endpoint first
            response = await client.get(
                f"{self.GITHUB_API_BASE}/orgs/{org}/repos",
                headers=self._get_headers(access_token),
                params={"per_page": 100, "sort": "updated"},
            )

            # If org endpoint returns 404, try user endpoint
            if response.status_code == 404:
                response = await client.get(
                    f"{self.GITHUB_API_BASE}/users/{org}/repos",
                    headers=self._get_headers(access_token),
                    params={"per_page": 100, "sort": "updated", "type": "owner"},
                )

            response.raise_for_status()

            rate_limit = self._parse_rate_limit(response)
            repos_data = response.json()

            repositories = [
                Repository(
                    id=str(repo["id"]),
                    name=repo["name"],
                    full_name=repo["full_name"],
                )
                for repo in repos_data
            ]

            return repositories, rate_limit

    async def get_repository_pull_requests(
        self, access_token: str, org: str, repo: str
    ) -> tuple[list[PullRequest], RateLimitInfo]:
        """Fetch open pull requests for a repository.

        This method fetches open PRs and their check statuses. Each PR's
        checks_status is determined by calling get_pull_request_checks.

        Args:
            access_token: GitHub OAuth access token.
            org: Organization or owner name.
            repo: Repository name.

        Returns:
            Tuple of (list of pull requests, rate limit info).

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{org}/{repo}/pulls",
                headers=self._get_headers(access_token),
                params={"state": "open", "per_page": 100},
            )
            response.raise_for_status()

            rate_limit = self._parse_rate_limit(response)
            prs_data = response.json()

            pull_requests = []
            for pr in prs_data:
                # Get check status for this PR
                checks_status = await self._get_pr_checks_status(
                    client, access_token, org, repo, pr["head"]["sha"]
                )

                pull_requests.append(
                    PullRequest(
                        number=pr["number"],
                        title=pr["title"],
                        author=Author(
                            username=pr["user"]["login"],
                            avatar_url=pr["user"].get("avatar_url"),
                        ),
                        labels=[
                            Label(name=label["name"], color=label["color"])
                            for label in pr.get("labels", [])
                        ],
                        checks_status=checks_status,
                        html_url=pr["html_url"],
                        created_at=datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")),
                    )
                )

            return pull_requests, rate_limit

    async def _get_pr_checks_status(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        org: str,
        repo: str,
        sha: str,
    ) -> str:
        """Fetch check status for a specific commit.

        Args:
            client: HTTP client to use for the request.
            access_token: GitHub OAuth access token.
            org: Organization or owner name.
            repo: Repository name.
            sha: Commit SHA to check.

        Returns:
            Aggregate check status: 'pass', 'fail', or 'pending'.
        """
        try:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{org}/{repo}/commits/{sha}/check-runs",
                headers=self._get_headers(access_token),
            )
            response.raise_for_status()

            data = response.json()
            check_runs = data.get("check_runs", [])

            if not check_runs:
                return "pending"

            # Aggregate status: any failure -> fail, any pending -> pending, else pass
            has_failure = False
            has_pending = False

            for check in check_runs:
                status = check.get("status")
                conclusion = check.get("conclusion")

                if status != "completed":
                    has_pending = True
                elif conclusion in ("failure", "cancelled", "timed_out"):
                    has_failure = True

            if has_failure:
                return "fail"
            if has_pending:
                return "pending"
            return "pass"

        except httpx.HTTPStatusError:
            # If we can't get check status, treat as pending
            return "pending"

    async def get_pull_request_checks(
        self, access_token: str, org: str, repo: str, pr_number: int
    ) -> tuple[str, RateLimitInfo]:
        """Fetch check status for a specific pull request.

        Args:
            access_token: GitHub OAuth access token.
            org: Organization or owner name.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            Tuple of (check status string, rate limit info).
            Status is one of: 'pass', 'fail', 'pending'.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        async with httpx.AsyncClient() as client:
            # First get the PR to find the head SHA
            pr_response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{org}/{repo}/pulls/{pr_number}",
                headers=self._get_headers(access_token),
            )
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            sha = pr_data["head"]["sha"]

            # Get check runs for the head commit
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{org}/{repo}/commits/{sha}/check-runs",
                headers=self._get_headers(access_token),
            )
            response.raise_for_status()

            rate_limit = self._parse_rate_limit(response)
            data = response.json()
            check_runs = data.get("check_runs", [])

            if not check_runs:
                return "pending", rate_limit

            # Aggregate status
            has_failure = False
            has_pending = False

            for check in check_runs:
                status = check.get("status")
                conclusion = check.get("conclusion")

                if status != "completed":
                    has_pending = True
                elif conclusion in ("failure", "cancelled", "timed_out"):
                    has_failure = True

            if has_failure:
                return "fail", rate_limit
            if has_pending:
                return "pending", rate_limit
            return "pass", rate_limit

    async def get_rate_limit(self, access_token: str) -> RateLimitInfo:
        """Fetch current rate limit status from GitHub API.

        Makes a lightweight API call to /rate_limit endpoint to get
        current rate limit information without counting against limits.

        Args:
            access_token: GitHub OAuth access token.

        Returns:
            RateLimitInfo with remaining requests and reset time.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/rate_limit",
                headers=self._get_headers(access_token),
            )
            response.raise_for_status()

            data = response.json()
            core = data.get("resources", {}).get("core", {})
            remaining = core.get("remaining", 0)
            reset_timestamp = core.get("reset", 0)
            reset_at = datetime.fromtimestamp(reset_timestamp, tz=UTC)

            return RateLimitInfo(remaining=remaining, reset_at=reset_at)

    # Required scopes for notification schedules
    REQUIRED_PAT_SCOPES = {"read:org", "repo"}

    async def validate_pat(self, pat: str) -> PATValidationResult:
        """Validate a GitHub Personal Access Token.

        Checks that the PAT is valid by calling the /user endpoint and
        verifies that it has the required scopes from the X-OAuth-Scopes header.

        Args:
            pat: GitHub Personal Access Token to validate.

        Returns:
            PATValidationResult containing validation status, scopes,
            and any missing required scopes.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.GITHUB_API_BASE}/user",
                    headers=self._get_headers(pat),
                )
                response.raise_for_status()

                # Parse user data
                user_data = response.json()
                username = user_data.get("login")

                # Parse scopes from response header
                # Classic PATs use X-OAuth-Scopes header
                # Fine-grained PATs don't have this header but work differently
                scopes_header = response.headers.get("X-OAuth-Scopes", "")
                if scopes_header:
                    scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
                else:
                    # Fine-grained PATs don't return scopes in header
                    # They have repository-level permissions instead
                    # We'll validate access via repository checks
                    scopes = []

                # Check for missing required scopes (only for classic PATs)
                missing_scopes = []
                if scopes:  # Classic PAT
                    scopes_set = set(scopes)
                    for required in self.REQUIRED_PAT_SCOPES:
                        if required not in scopes_set:
                            missing_scopes.append(required)

                return PATValidationResult(
                    is_valid=True,
                    scopes=scopes,
                    missing_scopes=missing_scopes,
                    username=username,
                    error_message=None,
                )

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return PATValidationResult(
                        is_valid=False,
                        scopes=[],
                        missing_scopes=[],
                        username=None,
                        error_message="Invalid or expired GitHub Personal Access Token",
                    )
                return PATValidationResult(
                    is_valid=False,
                    scopes=[],
                    missing_scopes=[],
                    username=None,
                    error_message=f"GitHub API error: {e.response.status_code}",
                )
            except httpx.RequestError as e:
                return PATValidationResult(
                    is_valid=False,
                    scopes=[],
                    missing_scopes=[],
                    username=None,
                    error_message=f"Failed to connect to GitHub API: {e!s}",
                )

    async def validate_repository_access(
        self, pat: str, repositories: list[RepositoryRef]
    ) -> RepositoryAccessResult:
        """Validate that a PAT can access the specified repositories.

        Checks each repository by attempting to fetch it from the GitHub API.

        Args:
            pat: GitHub Personal Access Token.
            repositories: List of repositories to check access for.

        Returns:
            RepositoryAccessResult with accessible and inaccessible repos.
        """
        accessible: list[RepositoryRef] = []
        inaccessible: list[InaccessibleRepository] = []

        async with httpx.AsyncClient() as client:
            for repo_ref in repositories:
                try:
                    response = await client.get(
                        f"{self.GITHUB_API_BASE}/repos/{repo_ref.organization}/{repo_ref.repository}",
                        headers=self._get_headers(pat),
                    )

                    if response.status_code == 200:
                        accessible.append(repo_ref)
                    elif response.status_code == 404:
                        inaccessible.append(
                            InaccessibleRepository(
                                organization=repo_ref.organization,
                                repository=repo_ref.repository,
                                reason="Repository not found or no access",
                            )
                        )
                    elif response.status_code == 403:
                        inaccessible.append(
                            InaccessibleRepository(
                                organization=repo_ref.organization,
                                repository=repo_ref.repository,
                                reason="Access forbidden - insufficient permissions",
                            )
                        )
                    else:
                        inaccessible.append(
                            InaccessibleRepository(
                                organization=repo_ref.organization,
                                repository=repo_ref.repository,
                                reason=f"GitHub API error: {response.status_code}",
                            )
                        )
                except httpx.RequestError as e:
                    inaccessible.append(
                        InaccessibleRepository(
                            organization=repo_ref.organization,
                            repository=repo_ref.repository,
                            reason=f"Connection error: {e!s}",
                        )
                    )

        return RepositoryAccessResult(accessible=accessible, inaccessible=inaccessible)


def get_github_api_service() -> GitHubAPIService:
    """Factory function for dependency injection.

    Returns:
        GitHubAPIService instance.
    """
    return GitHubAPIService()
