# PR-Review Application Specification

## Overview

PR-Review is a GitHub Pull Request monitoring application that helps developers track open PRs across their GitHub organizations. The application consists of three main components: a React frontend, a FastAPI backend, and a background scheduler for email notifications.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Web Frontend  │────▶│   Web Backend   │────▶│  GitHub API     │
│   (React/Vite)  │     │   (FastAPI)     │     │                 │
│                 │     │                 │     └─────────────────┘
└─────────────────┘     │                 │
                        │    ┌────────┐   │     ┌─────────────────┐
                        │    │ SQLite │   │     │                 │
                        │    └────────┘   │────▶│   SMTP2GO       │
                        │                 │     │                 │
┌─────────────────┐     │                 │     └─────────────────┘
│                 │     │                 │
│   Scheduler     │────▶│                 │
│   (APScheduler) │     │                 │
│                 │     └─────────────────┘
└─────────────────┘
```

## Components

### 1. Web Frontend (web-fe)

A single-page React application built with Vite and Tailwind CSS 4.

#### Pages

1. **Dashboard** (`/`)
   - Organization selector dropdown in navbar (populated from user's GitHub access)
   - List of repositories in selected organization
   - Under each repository: list of open PRs
   - Manual refresh button to trigger data refresh from GitHub

2. **Settings** (`/settings`)
   - User email address configuration
   - List of configured notification schedules
   - Add/edit/delete notification schedules

3. **Login** (`/login`)
   - GitHub OAuth login button
   - Redirects to dashboard on successful authentication

#### PR Display Fields

Each pull request displays:
- Title (as clickable link opening GitHub PR in new tab)
- Labels/tags (colored badges)
- Author (avatar and username)
- Checks status (single pass/fail icon)
- Date opened (relative format, e.g., "3 days ago")

#### Authentication Flow

1. User clicks "Login with GitHub"
2. Redirect to GitHub OAuth authorization
3. GitHub redirects back with authorization code
4. Backend exchanges code for access token
5. Backend creates JWT and returns to frontend
6. Frontend stores JWT in localStorage
7. JWT included in Authorization header for all API requests

### 2. Web Backend (web-be)

A Python FastAPI REST API.

#### Authentication

- GitHub OAuth 2.0 for user authentication
- JWT tokens for session management (stateless)
- JWT secret key via environment variable

#### API Endpoints

##### Auth
- `GET /api/auth/login` - Initiates GitHub OAuth flow
- `GET /api/auth/callback` - GitHub OAuth callback handler
- `GET /api/auth/me` - Returns current user info
- `POST /api/auth/logout` - Invalidates session (client-side JWT removal)

##### Organizations
- `GET /api/organizations` - List organizations user has access to

##### Repositories
- `GET /api/organizations/{org}/repositories` - List repositories in organization

##### Pull Requests
- `GET /api/organizations/{org}/repositories/{repo}/pulls` - List open PRs for repository
- `GET /api/pulls/refresh` - Trigger refresh of PR data from GitHub (returns rate limit info)

##### User Settings
- `GET /api/settings` - Get user settings (email address)
- `PUT /api/settings` - Update user settings

##### Notification Schedules
- `GET /api/schedules` - List user's notification schedules
- `POST /api/schedules` - Create new notification schedule
- `GET /api/schedules/{id}` - Get specific schedule
- `PUT /api/schedules/{id}` - Update schedule
- `DELETE /api/schedules/{id}` - Delete schedule

#### Database Schema

Using SQLite with Alembic migrations.

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,  -- GitHub user ID
    github_username TEXT NOT NULL,
    github_access_token TEXT NOT NULL,  -- Encrypted
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification schedules table
CREATE TABLE notification_schedules (
    id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    cron_expression TEXT NOT NULL,  -- e.g., "0 9 * * 1-5"
    github_pat TEXT NOT NULL,  -- Encrypted, for cron job GitHub access
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schedule repositories (many-to-many)
CREATE TABLE schedule_repositories (
    id TEXT PRIMARY KEY,  -- UUID
    schedule_id TEXT NOT NULL REFERENCES notification_schedules(id) ON DELETE CASCADE,
    organization TEXT NOT NULL,
    repository TEXT NOT NULL,
    UNIQUE(schedule_id, organization, repository)
);

-- Cached PR data (populated by cron job)
CREATE TABLE cached_pull_requests (
    id TEXT PRIMARY KEY,  -- UUID
    schedule_id TEXT NOT NULL REFERENCES notification_schedules(id) ON DELETE CASCADE,
    organization TEXT NOT NULL,
    repository TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    author_avatar_url TEXT,
    labels TEXT,  -- JSON array
    checks_status TEXT,  -- 'pass', 'fail', 'pending'
    html_url TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(schedule_id, organization, repository, pr_number)
);
```

#### Encryption

- PATs and GitHub access tokens encrypted using Fernet symmetric encryption
- Encryption key provided via `ENCRYPTION_KEY` environment variable
- Key must be a valid Fernet key (32 url-safe base64-encoded bytes)

#### Rate Limit Handling

- Track GitHub API rate limits silently
- When user triggers manual refresh, return rate limit status in response
- Queue requests appropriately to avoid hitting limits

### 3. Scheduler (scheduler)

A Python application using APScheduler that runs continuously.

#### Functionality

1. On startup, loads all active schedules from database
2. Creates APScheduler jobs for each schedule based on cron expression
3. Polls database periodically (every 60 seconds) for schedule changes
4. When a scheduled job runs:
   - Fetches open PRs from GitHub using the schedule's PAT
   - Caches PR data in database
   - If there are open PRs, sends summary email via SMTP2GO
   - If no open PRs, skips email
5. Logs errors without sending error emails

#### Email Content

Subject: `[PR-Review] Open Pull Requests Summary`

Body:
```
You have open pull requests that need attention.

Repository Summary:
- org/repo-1: 3 open PRs
- org/repo-2: 1 open PR

View details: {APPLICATION_URL}/

---
This is an automated message from PR-Review.
To manage your notification settings, visit {APPLICATION_URL}/settings
```

## Environment Variables

### Web Frontend
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_URL` | Backend API URL | Yes | - |

### Web Backend
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | SQLite database path | No | `sqlite:///./pr_review.db` |
| `GITHUB_CLIENT_ID` | GitHub OAuth App client ID | Yes | - |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App client secret | Yes | - |
| `GITHUB_REDIRECT_URI` | OAuth callback URL | Yes | - |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Yes | - |
| `JWT_ALGORITHM` | JWT algorithm | No | `HS256` |
| `JWT_EXPIRATION_HOURS` | JWT token expiration | No | `24` |
| `ENCRYPTION_KEY` | Fernet key for encrypting secrets | Yes | - |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | `http://localhost:5173` |

### Scheduler
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | SQLite database path | No | `sqlite:///./pr_review.db` |
| `ENCRYPTION_KEY` | Fernet key for decrypting PATs | Yes | - |
| `SMTP2GO_HOST` | SMTP2GO server hostname | Yes | - |
| `SMTP2GO_PORT` | SMTP2GO server port | No | `587` |
| `SMTP2GO_USERNAME` | SMTP2GO username | Yes | - |
| `SMTP2GO_PASSWORD` | SMTP2GO password | Yes | - |
| `EMAIL_FROM_ADDRESS` | Sender email address | Yes | - |
| `APPLICATION_URL` | Base URL of the application (for email links) | Yes | - |
| `SCHEDULE_POLL_INTERVAL` | Seconds between schedule DB polls | No | `60` |

## Project Structure

```
pr-review/
├── README.md
├── SPECIFICATION.md
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── ci.yml           # Build, lint, test
│       └── release.yml      # Docker image release
├── apps/
│   ├── web-fe/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   ├── tailwind.config.js
│   │   ├── index.html
│   │   ├── src/
│   │   │   ├── main.tsx
│   │   │   ├── App.tsx
│   │   │   ├── components/
│   │   │   │   ├── Navbar.tsx
│   │   │   │   ├── OrgSelector.tsx
│   │   │   │   ├── RepoList.tsx
│   │   │   │   ├── PullRequestCard.tsx
│   │   │   │   ├── ScheduleForm.tsx
│   │   │   │   └── ScheduleList.tsx
│   │   │   ├── pages/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── Settings.tsx
│   │   │   │   └── Login.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts
│   │   │   │   ├── useOrganizations.ts
│   │   │   │   ├── usePullRequests.ts
│   │   │   │   └── useSchedules.ts
│   │   │   ├── services/
│   │   │   │   └── api.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── utils/
│   │   │       └── date.ts
│   │   └── tests/
│   │       ├── components/
│   │       ├── pages/
│   │       └── hooks/
│   ├── web-be/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── alembic/
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   ├── src/
│   │   │   └── pr_review_api/
│   │   │       ├── __init__.py
│   │   │       ├── main.py
│   │   │       ├── config.py
│   │   │       ├── database.py
│   │   │       ├── models/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── user.py
│   │   │       │   ├── schedule.py
│   │   │       │   └── pull_request.py
│   │   │       ├── schemas/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── auth.py
│   │   │       │   ├── organization.py
│   │   │       │   ├── repository.py
│   │   │       │   ├── pull_request.py
│   │   │       │   └── schedule.py
│   │   │       ├── routers/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── auth.py
│   │   │       │   ├── organizations.py
│   │   │       │   ├── repositories.py
│   │   │       │   ├── pulls.py
│   │   │       │   ├── settings.py
│   │   │       │   └── schedules.py
│   │   │       ├── services/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── github.py
│   │   │       │   ├── encryption.py
│   │   │       │   └── jwt.py
│   │   │       └── dependencies.py
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_auth.py
│   │       ├── test_organizations.py
│   │       ├── test_pulls.py
│   │       ├── test_schedules.py
│   │       └── test_services/
│   │           ├── test_github.py
│   │           ├── test_encryption.py
│   │           └── test_jwt.py
│   └── scheduler/
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── src/
│       │   └── pr_review_scheduler/
│       │       ├── __init__.py
│       │       ├── main.py
│       │       ├── config.py
│       │       ├── scheduler.py
│       │       ├── jobs/
│       │       │   ├── __init__.py
│       │       │   └── pr_notification.py
│       │       └── services/
│       │           ├── __init__.py
│       │           ├── github.py
│       │           ├── email.py
│       │           └── database.py
│       └── tests/
│           ├── conftest.py
│           ├── test_scheduler.py
│           └── test_jobs/
│               └── test_pr_notification.py
└── shared/
    └── python/
        └── pr_review_shared/
            ├── pyproject.toml
            ├── src/
            │   └── pr_review_shared/
            │       ├── __init__.py
            │       ├── encryption.py
            │       └── models.py
            └── tests/
                └── test_encryption.py
```

## Development Workflow

### Git Workflow

All changes must follow this process:
1. Create a new branch from `main`
2. Make changes in small, focused commits
3. Push branch and create pull request using `gh pr create`
4. Merge after review (can self-merge for solo development)

### Incremental Development

Work should be completed in vertical slices. Suggested order:

#### Phase 1: Project Foundation
1. Initialize monorepo structure with README
2. Set up shared Python package with encryption utilities
3. Set up web-be project structure with FastAPI skeleton
4. Set up web-fe project structure with Vite/React/Tailwind
5. Set up scheduler project structure
6. Add Docker Compose configuration

#### Phase 2: CI/CD
7. Create GitHub Actions CI workflow (lint, test, build)
8. Create GitHub Actions release workflow

#### Phase 3: Authentication
9. Implement GitHub OAuth backend endpoints
10. Implement JWT service
11. Add database models and Alembic migrations for users
12. Implement login page and auth flow in frontend
13. Add auth context and protected routes

#### Phase 4: Core PR Display
14. Implement GitHub API service (organizations, repos, PRs)
15. Implement organizations endpoint
16. Implement repositories endpoint
17. Implement pull requests endpoint
18. Build dashboard page with org selector
19. Build repository list component
20. Build pull request card component
21. Implement manual refresh functionality

#### Phase 5: Notification Schedules
22. Add database models for schedules
23. Implement schedule CRUD endpoints
24. Implement PAT validation on schedule save
25. Build settings page
26. Build schedule form component
27. Build schedule list component

#### Phase 6: Scheduler Service
28. Implement APScheduler setup
29. Implement schedule loading from database
30. Implement PR fetching job
31. Implement email sending via SMTP2GO
32. Implement schedule change polling
33. Add PR caching to database

#### Phase 7: Polish
34. Add error handling and loading states
35. Add input validation
36. Final testing and bug fixes

## Testing Requirements

### Coverage Target
Aim for >90% code coverage across all components.

### Backend Testing
- Use pytest with pytest-asyncio for async tests
- Use httpx for testing FastAPI endpoints
- Mock GitHub API calls using responses or pytest-httpx
- Use factory_boy or similar for test data generation
- Test database operations with in-memory SQLite

### Frontend Testing
- Use Vitest as test runner
- Use React Testing Library for component tests
- Mock API calls using MSW (Mock Service Worker)
- Test custom hooks in isolation

### Scheduler Testing
- Mock APScheduler for unit tests
- Mock database and email services
- Test job execution logic independently

## Docker Configuration

### Dockerfiles

Each Dockerfile should:
- Use multi-stage builds for smaller images
- Use non-root user for security
- Include health checks where appropriate

### Docker Compose

```yaml
version: '3.8'

services:
  web-fe:
    build: ./apps/web-fe
    ports:
      - "5173:80"
    environment:
      - API_URL=http://localhost:8000
    depends_on:
      - web-be

  web-be:
    build: ./apps/web-be
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/pr_review.db
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/callback
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - CORS_ORIGINS=http://localhost:5173
    volumes:
      - ./data:/app/data

  scheduler:
    build: ./apps/scheduler
    environment:
      - DATABASE_URL=sqlite:///./data/pr_review.db
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - SMTP2GO_HOST=${SMTP2GO_HOST}
      - SMTP2GO_PORT=${SMTP2GO_PORT}
      - SMTP2GO_USERNAME=${SMTP2GO_USERNAME}
      - SMTP2GO_PASSWORD=${SMTP2GO_PASSWORD}
      - EMAIL_FROM_ADDRESS=${EMAIL_FROM_ADDRESS}
      - APPLICATION_URL=http://localhost:5173
    volumes:
      - ./data:/app/data
    depends_on:
      - web-be
```

## GitHub Actions

### CI Workflow (ci.yml)

Triggers: push to any branch, pull requests to main

Jobs:
1. **lint-backend**: Run ruff on Python code
2. **lint-frontend**: Run ESLint on TypeScript/React code
3. **test-backend**: Run pytest with coverage
4. **test-frontend**: Run Vitest with coverage
5. **test-scheduler**: Run pytest with coverage
6. **build-backend**: Verify Docker build succeeds
7. **build-frontend**: Verify Docker build succeeds
8. **build-scheduler**: Verify Docker build succeeds

### Release Workflow (release.yml)

Triggers: tags matching `v*.*.*`

Jobs:
1. Build and push `pr-review-web-fe` image
2. Build and push `pr-review-web-be` image
3. Build and push `pr-review-scheduler` image

Images tagged with:
- Version tag (e.g., `v1.0.0`)
- `latest`

## API Response Formats

### Standard Success Response
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

### Pull Request Response
```json
{
  "data": {
    "pulls": [
      {
        "number": 123,
        "title": "Add new feature",
        "author": {
          "username": "octocat",
          "avatar_url": "https://..."
        },
        "labels": [
          {
            "name": "enhancement",
            "color": "84b6eb"
          }
        ],
        "checks_status": "pass",
        "html_url": "https://github.com/org/repo/pull/123",
        "created_at": "2024-01-10T08:00:00Z"
      }
    ]
  },
  "meta": {
    "rate_limit": {
      "remaining": 4500,
      "reset_at": "2024-01-15T11:00:00Z"
    }
  }
}
```

### Schedule Response
```json
{
  "data": {
    "id": "uuid",
    "name": "Daily PR Check",
    "cron_expression": "0 9 * * 1-5",
    "repositories": [
      {
        "organization": "my-org",
        "repository": "my-repo"
      }
    ],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

## Security Considerations

1. **Token Storage**: All GitHub tokens (OAuth and PATs) encrypted at rest
2. **JWT Security**: Short-lived tokens, secure secret key
3. **PAT Validation**: Validate PATs have required scopes before saving
4. **Input Validation**: Validate all user inputs, especially cron expressions
5. **CORS**: Restrict to known frontend origins
6. **SQL Injection**: Use parameterized queries (handled by SQLAlchemy)
7. **Rate Limiting**: Implement rate limiting on API endpoints (future enhancement)

## Future Enhancements (Out of Scope)

- PR filtering by author, label, reviewer
- PR age warnings/highlighting
- Slack/Discord notifications
- Multiple email recipients per schedule
- PR review assignment suggestions
- Historical PR metrics/analytics
- Webhook-driven updates instead of polling
