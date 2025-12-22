# PROJECT-TASKS.md

Comprehensive task list for building the PR-Review application. Each phase must be completed in order, and tasks within each phase should generally be completed sequentially unless noted otherwise.

---

## Phase 1: Project Foundation

### Task 1.1: Initialize Monorepo Structure

**Description:** Create the base project structure with README and essential configuration files.

**Deliverables:**
- [x] Create root `README.md` with project overview, setup instructions, and architecture diagram
- [x] Create `.gitignore` with patterns for Python, Node.js, and IDE files
- [x] Create `apps/` directory structure
- [x] Create `shared/` directory structure
- [x] Create `.env.example` with all required environment variables

**Files to Create:**
```
pr-review/
├── README.md
├── .gitignore
├── .env.example
├── apps/
│   ├── web-fe/.gitkeep
│   ├── web-be/.gitkeep
│   └── scheduler/.gitkeep
└── shared/
    └── python/.gitkeep
```

**Acceptance Criteria:**
- Repository can be cloned and structure is clear
- README explains project purpose and architecture
- .env.example documents all required environment variables

---

### Task 1.2: Set Up Shared Python Package

**Description:** Create the shared Python package containing encryption utilities used by both web-be and scheduler.

**Deliverables:**
- [x] Create `pyproject.toml` with package configuration
- [x] Implement Fernet encryption/decryption utilities
- [x] Add unit tests for encryption module
- [x] Document usage in module docstrings

**Files to Create:**
```
shared/python/pr_review_shared/
├── pyproject.toml
├── src/
│   └── pr_review_shared/
│       ├── __init__.py
│       └── encryption.py
└── tests/
    └── test_encryption.py
```

**Implementation Details:**

`encryption.py` must provide:
- `encrypt_token(plaintext: str, key: str) -> str` - Encrypts a token using Fernet
- `decrypt_token(ciphertext: str, key: str) -> str` - Decrypts a token using Fernet
- `generate_encryption_key() -> str` - Generates a new valid Fernet key

**Acceptance Criteria:**
- Package can be installed with `pip install -e .`
- Encryption round-trip works correctly
- Invalid keys raise appropriate exceptions
- Tests pass with >90% coverage

---

### Task 1.3: Set Up Web Backend Project Structure

**Description:** Create the FastAPI backend project with basic skeleton and configuration.

**Deliverables:**
- [x] Create `pyproject.toml` with FastAPI and all dependencies
- [x] Create basic FastAPI application entry point
- [x] Set up configuration management with pydantic-settings
- [x] Set up SQLAlchemy database connection
- [x] Initialize Alembic for migrations
- [x] Create Dockerfile with multi-stage build
- [x] Add health check endpoint

**Files to Create:**
```
apps/web-be/
├── Dockerfile
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/.gitkeep
└── src/
    └── pr_review_api/
        ├── __init__.py
        ├── main.py
        ├── config.py
        ├── database.py
        └── dependencies.py
```

**Dependencies (pyproject.toml):**
- fastapi
- uvicorn[standard]
- sqlalchemy
- alembic
- pydantic-settings
- httpx (for GitHub API)
- python-jose[cryptography] (for JWT)
- pr-review-shared (local package)

**Dev Dependencies:**
- pytest
- pytest-asyncio
- pytest-cov
- httpx (for test client)
- ruff

**Configuration (config.py):**
```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./pr_review.db"
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    encryption_key: str
    cors_origins: str = "http://localhost:5173"
```

**Acceptance Criteria:**
- `uvicorn pr_review_api.main:app --reload` starts successfully
- `/health` endpoint returns `{"status": "ok"}`
- Alembic can create and run migrations
- Docker image builds successfully

---

### Task 1.4: Set Up Web Frontend Project Structure

**Description:** Create the React frontend project with Vite, TypeScript, and Tailwind CSS 4.

**Deliverables:**
- [x] Initialize Vite project with React and TypeScript
- [x] Configure Tailwind CSS 4
- [x] Set up project directory structure
- [x] Create base App component with React Router
- [x] Configure API service with environment variable
- [x] Create Dockerfile with multi-stage build (nginx for production)
- [x] Set up Vitest for testing

**Files to Create:**
```
apps/web-fe/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── nginx.conf
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── components/.gitkeep
    ├── pages/.gitkeep
    ├── hooks/.gitkeep
    ├── services/
    │   └── api.ts
    ├── types/
    │   └── index.ts
    └── utils/
        └── date.ts
```

**Package Dependencies:**
- react, react-dom
- react-router-dom
- @tanstack/react-query (for data fetching)
- date-fns (for date formatting)

**Dev Dependencies:**
- typescript
- @types/react, @types/react-dom
- vite
- @vitejs/plugin-react
- tailwindcss, postcss, autoprefixer
- vitest
- @testing-library/react
- @testing-library/jest-dom
- msw (Mock Service Worker)
- eslint, eslint-plugin-react-hooks

**api.ts Base Structure:**
```typescript
const API_URL = import.meta.env.VITE_API_URL;

export const api = {
  async get<T>(path: string): Promise<T> { ... },
  async post<T>(path: string, data: unknown): Promise<T> { ... },
  async put<T>(path: string, data: unknown): Promise<T> { ... },
  async delete(path: string): Promise<void> { ... },
};
```

**Acceptance Criteria:**
- `npm run dev` starts development server on port 5173
- Tailwind CSS classes work correctly
- TypeScript compilation succeeds without errors
- Docker image builds and serves static files via nginx

---

### Task 1.5: Set Up Scheduler Project Structure

**Description:** Create the APScheduler-based scheduler service project.

**Deliverables:**
- [x] Create `pyproject.toml` with APScheduler and dependencies
- [x] Create basic scheduler entry point
- [x] Set up configuration management
- [x] Create Dockerfile
- [x] Create placeholder for job implementations

**Files to Create:**
```
apps/scheduler/
├── Dockerfile
├── pyproject.toml
└── src/
    └── pr_review_scheduler/
        ├── __init__.py
        ├── main.py
        ├── config.py
        ├── scheduler.py
        ├── jobs/
        │   ├── __init__.py
        │   └── pr_notification.py
        └── services/
            ├── __init__.py
            ├── github.py
            ├── email.py
            └── database.py
```

**Dependencies:**
- apscheduler
- sqlalchemy
- httpx
- pr-review-shared (local package)

**Configuration (config.py):**
```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./pr_review.db"
    encryption_key: str
    smtp2go_host: str
    smtp2go_port: int = 587
    smtp2go_username: str
    smtp2go_password: str
    email_from_address: str
    application_url: str
    schedule_poll_interval: int = 60
```

**Acceptance Criteria:**
- `python -m pr_review_scheduler.main` starts without errors
- Scheduler initializes and can be configured to run jobs
- Docker image builds successfully

---

### Task 1.6: Add Docker Compose Configuration

**Description:** Create Docker Compose configuration to run all services together.

**Deliverables:**
- [x] Create `docker-compose.yml` with all three services
- [x] Configure shared volume for SQLite database
- [x] Set up environment variable passthrough
- [x] Configure service dependencies
- [x] Create `docker-compose.dev.yml` for development overrides (hot reload)

**Files to Create:**
```
pr-review/
├── docker-compose.yml
└── docker-compose.dev.yml
```

**Acceptance Criteria:**
- `docker compose up` starts all services
- Services can communicate with each other
- Database persists between restarts
- `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` enables hot reload

---

## Phase 2: CI/CD

### Task 2.1: Create GitHub Actions CI Workflow

**Description:** Set up continuous integration to lint, test, and build all components on every push.

**Deliverables:**
- [ ] Create `.github/workflows/ci.yml`
- [ ] Configure jobs for backend linting (ruff)
- [ ] Configure jobs for frontend linting (eslint)
- [ ] Configure jobs for backend tests (pytest + coverage)
- [ ] Configure jobs for frontend tests (vitest + coverage)
- [ ] Configure jobs for scheduler tests
- [ ] Configure jobs to verify Docker builds
- [ ] Add coverage reporting

**Files to Create:**
```
.github/
└── workflows/
    └── ci.yml
```

**CI Jobs:**
1. `lint-backend` - Run `ruff check` on `apps/web-be` and `apps/scheduler`
2. `lint-frontend` - Run `npm run lint` on `apps/web-fe`
3. `test-shared` - Run pytest on `shared/python/pr_review_shared`
4. `test-backend` - Run pytest with coverage on `apps/web-be`
5. `test-frontend` - Run vitest with coverage on `apps/web-fe`
6. `test-scheduler` - Run pytest with coverage on `apps/scheduler`
7. `build-images` - Build all Docker images (does not push)

**Triggers:**
- Push to any branch
- Pull requests to `main`

**Acceptance Criteria:**
- CI runs on every push and PR
- All lint checks pass
- All tests pass with coverage reports
- Docker builds succeed

---

### Task 2.2: Create GitHub Actions Release Workflow

**Description:** Set up release workflow to build and push Docker images when version tags are created.

**Deliverables:**
- [ ] Create `.github/workflows/release.yml`
- [ ] Configure Docker Hub (or GitHub Container Registry) authentication
- [ ] Build and push all three images with version tags
- [ ] Tag images with both version and `latest`

**Files to Create:**
```
.github/
└── workflows/
    └── release.yml
```

**Triggers:**
- Tags matching `v*.*.*` pattern

**Images to Build:**
- `pr-review-web-fe`
- `pr-review-web-be`
- `pr-review-scheduler`

**Acceptance Criteria:**
- Creating a tag like `v1.0.0` triggers the workflow
- All three images are built and pushed
- Images are tagged with both version (e.g., `v1.0.0`) and `latest`

---

## Phase 3: Authentication

### Task 3.1: Implement GitHub OAuth Backend Endpoints

**Description:** Create the authentication endpoints that handle GitHub OAuth flow.

**Deliverables:**
- [ ] Implement `GET /api/auth/login` - Returns GitHub OAuth authorization URL
- [ ] Implement `GET /api/auth/callback` - Exchanges code for token, creates/updates user, returns JWT
- [ ] Implement `GET /api/auth/me` - Returns current authenticated user info
- [ ] Implement `POST /api/auth/logout` - Client-side only, returns success
- [ ] Create auth router and register with main app
- [ ] Write comprehensive tests with mocked GitHub API

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── routers/
│   ├── __init__.py
│   └── auth.py
├── schemas/
│   ├── __init__.py
│   └── auth.py
└── services/
    └── github.py (partial - OAuth methods only)
```

**OAuth Flow:**
1. `/api/auth/login` returns: `{"url": "https://github.com/login/oauth/authorize?client_id=...&scope=read:org,repo"}`
2. User authorizes on GitHub, redirects to `/api/auth/callback?code=xxx`
3. Backend exchanges code for access token via GitHub API
4. Backend fetches user info from GitHub API
5. Backend creates/updates user in database (encrypt access token)
6. Backend generates JWT with user ID
7. Backend redirects to frontend with JWT as query parameter

**Schemas (auth.py):**
```python
class LoginResponse(BaseModel):
    url: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    avatar_url: Optional[str]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

**Acceptance Criteria:**
- OAuth flow works end-to-end (testable with real GitHub OAuth app)
- User is created in database on first login
- User access token is encrypted in database
- JWT is returned and can be decoded
- Tests cover all endpoints with mocked GitHub responses

---

### Task 3.2: Implement JWT Service

**Description:** Create the JWT service for token generation and validation.

**Deliverables:**
- [ ] Implement `create_token(user_id: str) -> str`
- [ ] Implement `verify_token(token: str) -> dict` (returns payload or raises)
- [ ] Create dependency for protected routes `get_current_user`
- [ ] Write unit tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── services/
│   └── jwt.py
└── dependencies.py (add get_current_user)
```

**JWT Payload:**
```python
{
    "sub": user_id,      # GitHub user ID
    "exp": expiration,   # UTC timestamp
    "iat": issued_at     # UTC timestamp
}
```

**Acceptance Criteria:**
- Tokens can be created and verified
- Expired tokens raise appropriate exception
- Invalid tokens raise appropriate exception
- `get_current_user` dependency extracts user from Authorization header

---

### Task 3.3: Add Database Models and Migrations for Users

**Description:** Create the SQLAlchemy models and Alembic migrations for the users table.

**Deliverables:**
- [ ] Create User SQLAlchemy model
- [ ] Create initial Alembic migration for users table
- [ ] Verify migration runs successfully

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── models/
│   ├── __init__.py
│   └── user.py
└── alembic/
    └── versions/
        └── 001_create_users_table.py
```

**User Model:**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # GitHub user ID
    github_username = Column(String, nullable=False)
    github_access_token = Column(String, nullable=False)  # Encrypted
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Acceptance Criteria:**
- `alembic upgrade head` creates the users table
- `alembic downgrade -1` removes the table
- Model can be used to create and query users

---

### Task 3.4: Implement Login Page and Auth Flow in Frontend

**Description:** Create the login page with GitHub OAuth button and handle the callback.

**Deliverables:**
- [ ] Create Login page component
- [ ] Implement "Login with GitHub" button that redirects to backend `/api/auth/login`
- [ ] Create callback handler that extracts JWT from URL and stores in localStorage
- [ ] Redirect to dashboard after successful login
- [ ] Handle login errors gracefully

**Files to Create/Modify:**
```
apps/web-fe/src/
├── pages/
│   └── Login.tsx
├── services/
│   └── api.ts (add auth methods)
└── App.tsx (add login route)
```

**Flow:**
1. User visits `/login`
2. User clicks "Login with GitHub"
3. Frontend calls `/api/auth/login`, gets GitHub URL
4. Frontend redirects to GitHub
5. User authorizes, GitHub redirects to backend callback
6. Backend redirects to frontend `/?token=xxx`
7. Frontend extracts token, stores in localStorage, redirects to dashboard

**Acceptance Criteria:**
- Login page renders with GitHub login button
- Clicking button initiates OAuth flow
- Token is stored in localStorage after successful auth
- User is redirected to dashboard

---

### Task 3.5: Add Auth Context and Protected Routes

**Description:** Create React context for authentication state and protect routes that require login.

**Deliverables:**
- [ ] Create AuthContext with user state and auth methods
- [ ] Create `useAuth` hook for accessing auth state
- [ ] Create ProtectedRoute wrapper component
- [ ] Update api.ts to include JWT in Authorization header
- [ ] Add logout functionality
- [ ] Write tests for auth hooks

**Files to Create/Modify:**
```
apps/web-fe/src/
├── hooks/
│   └── useAuth.ts
├── components/
│   └── ProtectedRoute.tsx
├── services/
│   └── api.ts (add auth header)
└── App.tsx (wrap with AuthProvider)
```

**AuthContext Shape:**
```typescript
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => void;
}
```

**Acceptance Criteria:**
- Protected routes redirect to login if not authenticated
- User state is restored from localStorage on page refresh
- API calls include Authorization header when authenticated
- Logout clears token and redirects to login

---

## Phase 4: Core PR Display

### Task 4.1: Implement GitHub API Service

**Description:** Create the service for fetching organizations, repositories, and pull requests from GitHub API.

**Deliverables:**
- [ ] Implement `get_user_organizations(access_token) -> List[Organization]`
- [ ] Implement `get_organization_repositories(access_token, org) -> List[Repository]`
- [ ] Implement `get_repository_pull_requests(access_token, org, repo) -> List[PullRequest]`
- [ ] Implement `get_pull_request_checks(access_token, org, repo, pr_number) -> CheckStatus`
- [ ] Handle rate limiting (track remaining requests)
- [ ] Write tests with mocked GitHub responses

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── services/
│   └── github.py (extend with org/repo/PR methods)
└── schemas/
    ├── organization.py
    ├── repository.py
    └── pull_request.py
```

**GitHub API Endpoints Used:**
- `GET /user/orgs` - User's organizations
- `GET /orgs/{org}/repos` - Organization repositories
- `GET /repos/{org}/{repo}/pulls?state=open` - Open pull requests
- `GET /repos/{org}/{repo}/commits/{ref}/check-runs` - PR check status

**Rate Limit Handling:**
- Parse `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- Return rate limit info in service responses

**Acceptance Criteria:**
- All GitHub API methods work with valid access token
- Rate limit info is tracked and available
- Tests cover success and error cases

---

### Task 4.2: Implement Organizations Endpoint

**Description:** Create the API endpoint to list organizations the user has access to.

**Deliverables:**
- [ ] Implement `GET /api/organizations`
- [ ] Return list of organizations with id, name, and avatar_url
- [ ] Require authentication
- [ ] Write endpoint tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── routers/
│   └── organizations.py
└── main.py (register router)
```

**Response Format:**
```json
{
  "data": {
    "organizations": [
      {
        "id": "12345",
        "login": "my-org",
        "avatar_url": "https://avatars.githubusercontent.com/..."
      }
    ]
  }
}
```

**Acceptance Criteria:**
- Endpoint requires authentication
- Returns organizations from GitHub API
- Tests verify response format

---

### Task 4.3: Implement Repositories Endpoint

**Description:** Create the API endpoint to list repositories in an organization.

**Deliverables:**
- [ ] Implement `GET /api/organizations/{org}/repositories`
- [ ] Return list of repositories with id, name, full_name
- [ ] Require authentication
- [ ] Write endpoint tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── routers/
│   └── repositories.py
└── main.py (register router)
```

**Response Format:**
```json
{
  "data": {
    "repositories": [
      {
        "id": "67890",
        "name": "my-repo",
        "full_name": "my-org/my-repo"
      }
    ]
  }
}
```

**Acceptance Criteria:**
- Endpoint requires authentication
- Returns repositories from GitHub API
- Tests verify response format

---

### Task 4.4: Implement Pull Requests Endpoint

**Description:** Create the API endpoint to list open pull requests for a repository.

**Deliverables:**
- [ ] Implement `GET /api/organizations/{org}/repositories/{repo}/pulls`
- [ ] Return list of PRs with all display fields
- [ ] Include checks status for each PR
- [ ] Return rate limit info in meta
- [ ] Require authentication
- [ ] Write endpoint tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── routers/
│   └── pulls.py
└── main.py (register router)
```

**Response Format:**
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
          {"name": "enhancement", "color": "84b6eb"}
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

**Acceptance Criteria:**
- Endpoint requires authentication
- Returns PRs with checks status from GitHub API
- Rate limit info included in response
- Tests verify response format

---

### Task 4.5: Build Dashboard Page with Organization Selector

**Description:** Create the main dashboard page with navbar and organization selector dropdown.

**Deliverables:**
- [ ] Create Dashboard page component
- [ ] Create Navbar component with user avatar and logout
- [ ] Create OrgSelector dropdown component
- [ ] Implement `useOrganizations` hook to fetch organizations
- [ ] Store selected organization in state (and localStorage for persistence)
- [ ] Write component tests

**Files to Create/Modify:**
```
apps/web-fe/src/
├── pages/
│   └── Dashboard.tsx
├── components/
│   ├── Navbar.tsx
│   └── OrgSelector.tsx
├── hooks/
│   └── useOrganizations.ts
└── App.tsx (add dashboard route)
```

**Dashboard Layout:**
```
┌─────────────────────────────────────────────┐
│  Navbar: [OrgSelector ▼]    [Refresh] [👤]  │
├─────────────────────────────────────────────┤
│                                             │
│  Repository List                            │
│  (populated after org selected)             │
│                                             │
└─────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- Dashboard displays after login
- Organization dropdown loads and shows user's orgs
- Selecting an org updates state
- Selected org persists on page refresh

---

### Task 4.6: Build Repository List Component

**Description:** Create the component that displays repositories and their pull requests.

**Deliverables:**
- [ ] Create RepoList component
- [ ] Create usePullRequests hook to fetch PRs for selected org
- [ ] Display repositories as collapsible sections
- [ ] Show PR count badge for each repository
- [ ] Handle loading and empty states
- [ ] Write component tests

**Files to Create/Modify:**
```
apps/web-fe/src/
├── components/
│   └── RepoList.tsx
└── hooks/
    └── usePullRequests.ts
```

**Layout:**
```
┌─────────────────────────────────────────────┐
│  ▼ my-org/repo-1                        (3) │
│    ├── PullRequestCard                      │
│    ├── PullRequestCard                      │
│    └── PullRequestCard                      │
├─────────────────────────────────────────────┤
│  ▶ my-org/repo-2                        (1) │
└─────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- Repositories are displayed for selected organization
- Each repository shows count of open PRs
- Clicking repository expands/collapses PR list
- Loading spinner shown while fetching

---

### Task 4.7: Build Pull Request Card Component

**Description:** Create the component that displays individual pull request details.

**Deliverables:**
- [ ] Create PullRequestCard component
- [ ] Display title as clickable link (opens GitHub in new tab)
- [ ] Display colored label badges
- [ ] Display author avatar and username
- [ ] Display checks status icon (✓ green / ✗ red / ● yellow)
- [ ] Display relative time (e.g., "3 days ago") using date-fns
- [ ] Write component tests

**Files to Create/Modify:**
```
apps/web-fe/src/
├── components/
│   └── PullRequestCard.tsx
└── utils/
    └── date.ts
```

**Card Layout:**
```
┌─────────────────────────────────────────────┐
│  ✓  Add authentication feature    3 days ago│
│     [enhancement] [high-priority]           │
│     👤 octocat                              │
└─────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- All PR fields displayed correctly
- Title links to GitHub PR page
- Labels rendered with correct colors
- Check status icon reflects pass/fail/pending
- Dates formatted as relative time

---

### Task 4.8: Implement Manual Refresh Functionality

**Description:** Add refresh button to manually re-fetch PR data from GitHub.

**Deliverables:**
- [ ] Add refresh button to navbar
- [ ] Implement `GET /api/pulls/refresh` endpoint (or trigger via existing endpoints)
- [ ] Show loading state during refresh
- [ ] Display rate limit info after refresh
- [ ] Handle rate limit exceeded gracefully
- [ ] Write tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/routers/pulls.py (add refresh endpoint)
apps/web-fe/src/components/Navbar.tsx (add refresh button)
```

**Acceptance Criteria:**
- Clicking refresh re-fetches data from GitHub
- Loading indicator shown during refresh
- Rate limit info displayed (e.g., "4500 requests remaining, resets in 45 min")
- User notified if rate limit exceeded

---

## Phase 5: Notification Schedules

### Task 5.1: Add Database Models for Schedules

**Description:** Create SQLAlchemy models and migrations for notification schedules.

**Deliverables:**
- [ ] Create NotificationSchedule model
- [ ] Create ScheduleRepository model (many-to-many)
- [ ] Create CachedPullRequest model
- [ ] Create Alembic migration
- [ ] Write model tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── models/
│   ├── schedule.py
│   └── pull_request.py
└── alembic/
    └── versions/
        └── 002_create_schedules_tables.py
```

**Models:**
```python
class NotificationSchedule(Base):
    __tablename__ = "notification_schedules"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)
    github_pat = Column(String, nullable=False)  # Encrypted
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repositories = relationship("ScheduleRepository", back_populates="schedule")

class ScheduleRepository(Base):
    __tablename__ = "schedule_repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    schedule_id = Column(String, ForeignKey("notification_schedules.id", ondelete="CASCADE"))
    organization = Column(String, nullable=False)
    repository = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("schedule_id", "organization", "repository"),)
```

**Acceptance Criteria:**
- Migration creates all three tables with correct constraints
- Foreign keys work correctly with cascade delete
- Models can be used to create and query schedules

---

### Task 5.2: Implement Schedule CRUD Endpoints

**Description:** Create the API endpoints for managing notification schedules.

**Deliverables:**
- [ ] Implement `GET /api/schedules` - List user's schedules
- [ ] Implement `POST /api/schedules` - Create new schedule
- [ ] Implement `GET /api/schedules/{id}` - Get specific schedule
- [ ] Implement `PUT /api/schedules/{id}` - Update schedule
- [ ] Implement `DELETE /api/schedules/{id}` - Delete schedule
- [ ] Create Pydantic schemas for request/response
- [ ] Write endpoint tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── routers/
│   └── schedules.py
├── schemas/
│   └── schedule.py
└── main.py (register router)
```

**Request Schema (Create/Update):**
```python
class ScheduleCreate(BaseModel):
    name: str
    cron_expression: str
    github_pat: str
    repositories: List[RepositoryRef]
    is_active: bool = True

class RepositoryRef(BaseModel):
    organization: str
    repository: str
```

**Acceptance Criteria:**
- All CRUD operations work correctly
- User can only access their own schedules
- PAT is encrypted before storage
- Tests cover all endpoints

---

### Task 5.3: Implement PAT Validation on Schedule Save

**Description:** Validate GitHub Personal Access Token when saving a schedule.

**Deliverables:**
- [ ] Add PAT validation method to GitHub service
- [ ] Check PAT has required scopes (read:org, repo)
- [ ] Test PAT can access specified repositories
- [ ] Return meaningful error if validation fails
- [ ] Write tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── services/
│   └── github.py (add validate_pat method)
└── routers/
    └── schedules.py (call validation before save)
```

**Validation Steps:**
1. Call GitHub API with PAT to verify it's valid
2. Check token scopes include `read:org` and `repo`
3. For each repository in schedule, verify access

**Acceptance Criteria:**
- Invalid PAT returns 400 with clear error message
- Missing scopes returns 400 with list of required scopes
- Inaccessible repositories listed in error response

---

### Task 5.4: Implement User Settings Endpoints

**Description:** Create endpoints for managing user settings (email address).

**Deliverables:**
- [ ] Implement `GET /api/settings` - Get user's email
- [ ] Implement `PUT /api/settings` - Update user's email
- [ ] Validate email format
- [ ] Write tests

**Files to Create/Modify:**
```
apps/web-be/src/pr_review_api/
├── routers/
│   └── settings.py
└── schemas/
    └── settings.py
```

**Acceptance Criteria:**
- User can read and update their email
- Invalid email format returns 400
- Tests cover endpoints

---

### Task 5.5: Build Settings Page

**Description:** Create the settings page for managing email and notification schedules.

**Deliverables:**
- [ ] Create Settings page component
- [ ] Add email address input with save button
- [ ] Add section for notification schedules
- [ ] Add navigation link in navbar
- [ ] Write page tests

**Files to Create/Modify:**
```
apps/web-fe/src/
├── pages/
│   └── Settings.tsx
├── components/
│   └── Navbar.tsx (add settings link)
└── App.tsx (add settings route)
```

**Page Layout:**
```
┌─────────────────────────────────────────────┐
│  Settings                                   │
├─────────────────────────────────────────────┤
│  Email Address                              │
│  [user@example.com        ] [Save]          │
├─────────────────────────────────────────────┤
│  Notification Schedules            [+ Add]  │
│  ┌─────────────────────────────────────┐    │
│  │ ScheduleList                        │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- Settings page accessible from navbar
- Email can be viewed and updated
- Schedule list displayed (next task)

---

### Task 5.6: Build Schedule Form Component

**Description:** Create the form for creating and editing notification schedules.

**Deliverables:**
- [ ] Create ScheduleForm component (modal or separate page)
- [ ] Add name input field
- [ ] Add cron expression input with helper text
- [ ] Add GitHub PAT input (masked)
- [ ] Add repository selector (multi-select from available repos)
- [ ] Add active toggle
- [ ] Implement form validation
- [ ] Implement save handler
- [ ] Write component tests

**Files to Create/Modify:**
```
apps/web-fe/src/
├── components/
│   └── ScheduleForm.tsx
└── hooks/
    └── useSchedules.ts
```

**Form Fields:**
- Name: text input, required
- Cron Expression: text input with examples (e.g., "0 9 * * 1-5" for weekdays at 9am)
- GitHub PAT: password input, required
- Repositories: multi-select dropdown
- Active: toggle switch

**Acceptance Criteria:**
- Form validates all required fields
- PAT input is masked
- Cron expression has helpful examples
- Repository selector loads available repos
- Form can be used for create and edit

---

### Task 5.7: Build Schedule List Component

**Description:** Create the component that displays list of notification schedules with actions.

**Deliverables:**
- [ ] Create ScheduleList component
- [ ] Display schedule name, cron expression (human readable), status
- [ ] Add edit button for each schedule
- [ ] Add delete button with confirmation
- [ ] Add toggle for active/inactive
- [ ] Write component tests

**Files to Create/Modify:**
```
apps/web-fe/src/
└── components/
    └── ScheduleList.tsx
```

**List Item Layout:**
```
┌─────────────────────────────────────────────┐
│  Daily PR Check                     [Active]│
│  Every weekday at 9:00 AM                   │
│  3 repositories                [Edit] [🗑️] │
└─────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- Schedules listed with all relevant info
- Cron expression displayed in human-readable format
- Edit opens form with pre-filled data
- Delete shows confirmation dialog
- Toggle updates active status immediately

---

## Phase 6: Scheduler Service

### Task 6.1: Implement APScheduler Setup

**Description:** Configure APScheduler with the job store and executor.

**Deliverables:**
- [ ] Create scheduler instance with appropriate job store
- [ ] Configure timezone handling
- [ ] Implement graceful shutdown
- [ ] Add basic logging
- [ ] Write tests

**Files to Create/Modify:**
```
apps/scheduler/src/pr_review_scheduler/
├── scheduler.py
└── main.py
```

**Configuration:**
- Use SQLAlchemy job store (or memory for simplicity)
- Use AsyncIOExecutor or ThreadPoolExecutor
- Handle SIGTERM/SIGINT for graceful shutdown

**Acceptance Criteria:**
- Scheduler starts and runs jobs
- Jobs persist across restarts (if using persistent store)
- Clean shutdown on termination signal

---

### Task 6.2: Implement Schedule Loading from Database

**Description:** Load active schedules from database and create APScheduler jobs.

**Deliverables:**
- [ ] Create database service to query schedules
- [ ] Convert cron expressions to APScheduler triggers
- [ ] Create jobs for each active schedule
- [ ] Handle schedule enable/disable
- [ ] Write tests

**Files to Create/Modify:**
```
apps/scheduler/src/pr_review_scheduler/
├── services/
│   └── database.py
└── scheduler.py
```

**Implementation:**
```python
def load_schedules():
    schedules = db.get_active_schedules()
    for schedule in schedules:
        scheduler.add_job(
            run_notification_job,
            CronTrigger.from_crontab(schedule.cron_expression),
            id=schedule.id,
            args=[schedule.id]
        )
```

**Acceptance Criteria:**
- All active schedules loaded on startup
- Inactive schedules not loaded
- Jobs run at correct times based on cron expression

---

### Task 6.3: Implement PR Fetching Job

**Description:** Create the job that fetches open PRs for a schedule's repositories.

**Deliverables:**
- [ ] Create notification job function
- [ ] Decrypt PAT from schedule
- [ ] Fetch PRs for each repository in schedule
- [ ] Aggregate results
- [ ] Handle errors gracefully (log, don't crash)
- [ ] Write tests

**Files to Create/Modify:**
```
apps/scheduler/src/pr_review_scheduler/
├── jobs/
│   └── pr_notification.py
└── services/
    └── github.py
```

**Job Flow:**
1. Load schedule from database
2. Decrypt GitHub PAT
3. For each repository in schedule:
   - Fetch open PRs via GitHub API
   - Add to results
4. If PRs found, proceed to email step
5. If no PRs, log and skip email

**Acceptance Criteria:**
- Job fetches PRs for all repositories in schedule
- PAT is decrypted successfully
- Errors logged but don't stop other jobs
- Empty results handled gracefully

---

### Task 6.4: Implement Email Sending via SMTP2GO

**Description:** Create the service to send notification emails.

**Deliverables:**
- [ ] Create email service with SMTP2GO configuration
- [ ] Implement `send_notification_email(to: str, subject: str, body: str)`
- [ ] Create email template for PR summary
- [ ] Handle SMTP errors gracefully
- [ ] Write tests

**Files to Create/Modify:**
```
apps/scheduler/src/pr_review_scheduler/
└── services/
    └── email.py
```

**Email Template:**
```
Subject: [PR-Review] Open Pull Requests Summary

You have open pull requests that need attention.

Repository Summary:
- org/repo-1: 3 open PRs
- org/repo-2: 1 open PR

View details: {APPLICATION_URL}/

---
This is an automated message from PR-Review.
To manage your notification settings, visit {APPLICATION_URL}/settings
```

**Acceptance Criteria:**
- Emails sent successfully via SMTP2GO
- Email content matches template
- SMTP errors logged but don't crash job

---

### Task 6.5: Implement Schedule Change Polling

**Description:** Poll database for schedule changes and update APScheduler jobs accordingly.

**Deliverables:**
- [ ] Create polling loop (every 60 seconds)
- [ ] Detect new schedules and add jobs
- [ ] Detect deleted schedules and remove jobs
- [ ] Detect updated schedules and update jobs
- [ ] Detect active/inactive changes
- [ ] Write tests

**Files to Create/Modify:**
```
apps/scheduler/src/pr_review_scheduler/
├── scheduler.py
└── services/
    └── database.py
```

**Polling Logic:**
```python
async def poll_for_changes():
    while True:
        current_schedules = db.get_all_schedules()
        current_jobs = {job.id for job in scheduler.get_jobs()}

        for schedule in current_schedules:
            if schedule.is_active and schedule.id not in current_jobs:
                add_job(schedule)
            elif not schedule.is_active and schedule.id in current_jobs:
                scheduler.remove_job(schedule.id)
            elif schedule.id in current_jobs:
                update_job_if_changed(schedule)

        # Remove jobs for deleted schedules
        for job_id in current_jobs:
            if not any(s.id == job_id for s in current_schedules):
                scheduler.remove_job(job_id)

        await asyncio.sleep(config.schedule_poll_interval)
```

**Acceptance Criteria:**
- New schedules picked up within poll interval
- Deleted schedules' jobs removed
- Updated schedules (cron, active status) reflected
- No duplicate jobs created

---

### Task 6.6: Add PR Caching to Database

**Description:** Cache fetched PR data in the database for potential future use.

**Deliverables:**
- [ ] Create cached_pull_requests table operations
- [ ] Store fetched PRs after each job run
- [ ] Clear old cached data before inserting new
- [ ] Write tests

**Files to Create/Modify:**
```
apps/scheduler/src/pr_review_scheduler/
├── services/
│   └── database.py
└── jobs/
    └── pr_notification.py
```

**Cache Strategy:**
- Delete existing cached PRs for schedule before insert
- Insert all current open PRs
- Store minimal data needed for email/display

**Acceptance Criteria:**
- PRs cached after each job run
- Old data replaced with fresh data
- Cache queryable for debugging

---

## Phase 7: Polish

### Task 7.1: Add Error Handling and Loading States

**Description:** Ensure all components handle errors gracefully and show appropriate loading states.

**Deliverables:**
- [ ] Add error boundaries to React app
- [ ] Create error display components
- [ ] Add loading spinners/skeletons to all async operations
- [ ] Handle API errors in all hooks
- [ ] Display user-friendly error messages
- [ ] Write tests for error states

**Files to Modify:**
```
apps/web-fe/src/
├── components/
│   ├── ErrorBoundary.tsx
│   ├── LoadingSpinner.tsx
│   └── ErrorMessage.tsx
└── hooks/
    └── *.ts (add error handling)
```

**Acceptance Criteria:**
- No unhandled promise rejections
- All API errors show user-friendly message
- Loading states visible during data fetching
- App doesn't crash on errors

---

### Task 7.2: Add Input Validation

**Description:** Add comprehensive input validation to all forms.

**Deliverables:**
- [ ] Validate email format in settings
- [ ] Validate cron expression syntax in schedule form
- [ ] Validate PAT format (basic check)
- [ ] Add validation to backend endpoints
- [ ] Display validation errors inline in forms
- [ ] Write validation tests

**Frontend Validation:**
- Email: RFC 5322 format
- Cron: Valid cron syntax (5 fields)
- PAT: Starts with "ghp_" or "github_pat_"

**Backend Validation:**
- All frontend validations mirrored
- Additional security validations

**Acceptance Criteria:**
- Invalid inputs show clear error messages
- Form submission blocked until valid
- Backend rejects invalid inputs with 400

---

### Task 7.3: Final Testing and Bug Fixes

**Description:** Complete test coverage, fix any remaining bugs, and prepare for release.

**Deliverables:**
- [ ] Achieve >90% test coverage across all components
- [ ] Fix any failing tests
- [ ] Manual end-to-end testing
- [ ] Fix discovered bugs
- [ ] Update documentation
- [ ] Verify Docker Compose works for full setup
- [ ] Update README with final instructions

**Testing Checklist:**
- [ ] Login/logout flow works
- [ ] Dashboard loads organizations and PRs
- [ ] Manual refresh works
- [ ] Settings can be updated
- [ ] Schedules can be created, edited, deleted
- [ ] Scheduler runs jobs on time
- [ ] Emails are sent correctly
- [ ] All error cases handled

**Acceptance Criteria:**
- All tests pass
- Coverage meets target
- No critical bugs
- Documentation complete
- Application ready for deployment

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 | 1.1 - 1.6 | Project foundation and structure |
| Phase 2 | 2.1 - 2.2 | CI/CD pipelines |
| Phase 3 | 3.1 - 3.5 | Authentication system |
| Phase 4 | 4.1 - 4.8 | Core PR display functionality |
| Phase 5 | 5.1 - 5.7 | Notification schedule management |
| Phase 6 | 6.1 - 6.6 | Background scheduler service |
| Phase 7 | 7.1 - 7.3 | Polish and finalization |

**Total Tasks:** 36
