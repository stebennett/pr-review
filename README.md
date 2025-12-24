# PR-Review

A GitHub Pull Request monitoring application that helps developers track open PRs across their GitHub organizations.

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

- **web-fe**: React frontend built with Vite and Tailwind CSS 4
- **web-be**: Python FastAPI REST API
- **scheduler**: Python APScheduler service for email notifications

## Project Structure

```
pr-review/
├── apps/
│   ├── web-fe/              # React frontend
│   ├── web-be/              # FastAPI backend
│   └── scheduler/           # APScheduler service
├── shared/
│   └── python/              # Shared Python packages
├── data/                    # SQLite database (gitignored)
├── docs/
│   ├── SPECIFICATION.md     # Full specification
│   └── PROJECT-TASKS.md     # Task breakdown
├── docker-compose.yml       # Production container orchestration
└── docker-compose.dev.yml   # Development overrides (hot reload)
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker and Docker Compose (optional, for containerized deployment)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-org/pr-review.git
cd pr-review
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start with Docker Compose

**Production mode:**
```bash
docker compose up
```

**Development mode (with hot reload):**
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Run a single service:**
```bash
docker compose up web-be       # Start backend only
docker compose up web-fe       # Start frontend only
docker compose up scheduler    # Start scheduler only
```

Or run each component individually (see Development Commands below).

## Local Development Setup

### 1. Create a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install the shared package

```bash
pip install -e ./shared/python/pr_review_shared
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and configure:

```bash
# Generate JWT secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Set up GitHub OAuth (required for authentication)

1. Go to https://github.com/settings/developers
2. Click **"New OAuth App"**
3. Fill in:
   - **Application name**: `PR-Review Local`
   - **Homepage URL**: `http://localhost:5173`
   - **Authorization callback URL**: `http://localhost:8000/api/auth/callback`
4. Copy the **Client ID** and generate a **Client Secret**
5. Add them to your `.env` file

## Development Commands

### Frontend (apps/web-fe)

```bash
cd apps/web-fe
npm install                    # Install dependencies
npm run dev                    # Start dev server (port 5173)
npm run build                  # Production build
npm run lint                   # Run ESLint
npm run test                   # Run Vitest tests
```

### Backend (apps/web-be)

```bash
cd apps/web-be
ln -s ../../.env .env          # Symlink .env for local development
pip install -e ".[dev]"        # Install with dev dependencies
uvicorn pr_review_api.main:app --reload  # Start dev server (port 8000)
ruff check .                   # Lint Python code
ruff format .                  # Format Python code
pytest                         # Run all tests
alembic upgrade head           # Run database migrations
```

The API documentation is available at http://localhost:8000/docs when the server is running.

### Scheduler (apps/scheduler)

```bash
cd apps/scheduler
pip install -e ".[dev]"        # Install with dev dependencies
python -m pr_review_scheduler.main  # Run scheduler
pytest                         # Run tests
```

## Environment Variables

See [.env.example](.env.example) for all required environment variables.

Key variables:
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: GitHub OAuth App credentials
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `ENCRYPTION_KEY`: Fernet key for encrypting sensitive data
- `SMTP2GO_*`: SMTP2GO credentials for email notifications

## License

MIT License - see [LICENSE](LICENSE) for details.
