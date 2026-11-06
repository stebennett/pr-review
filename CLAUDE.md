# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PR-Review is a GitHub Pull Request monitoring application with three main components:
- **web-fe**: React frontend (Vite + Tailwind CSS 4)
- **web-be**: Python FastAPI REST API
- **scheduler**: Python APScheduler service for email notifications

See `docs/SPECIFICATION.md` for the complete specification and architecture.

## Development Commands

### Frontend (apps/web-fe)
```bash
npm install                    # Install dependencies
npm run dev                    # Start dev server (port 5173)
npm run build                  # Production build
npm run lint                   # Run ESLint
npm run test                   # Run Vitest tests
npm run test -- --run <file>   # Run a single test file
```

### Backend (apps/web-be)
```bash
cd apps/web-be
pip install -e ".[dev]"        # Install with dev dependencies
uvicorn pr_review_api.main:app --reload  # Start dev server (port 8000)
ruff check .                   # Lint Python code
ruff format .                  # Format Python code
pytest                         # Run all tests
pytest tests/test_auth.py      # Run a single test file
pytest -k "test_name"          # Run tests matching pattern
alembic upgrade head           # Run database migrations
alembic revision --autogenerate -m "description"  # Create migration
```

### Scheduler (apps/scheduler)
```bash
cd apps/scheduler
pip install -e ".[dev]"        # Install with dev dependencies
python -m pr_review_scheduler.main  # Run scheduler
pytest                         # Run tests
```

### Docker
```bash
docker compose up              # Start all services
docker compose up web-be       # Start single service
docker compose build           # Rebuild images
```

## Architecture

```
web-fe (React/Vite) → web-be (FastAPI) → GitHub API
                           ↓
                        SQLite
                           ↑
scheduler (APScheduler) → SMTP2GO
```

### Backend Structure
- `routers/`: API endpoint handlers (auth, organizations, repositories, pulls, settings, schedules)
- `services/`: Business logic (github.py, encryption.py, jwt.py)
- `models/`: SQLAlchemy database models
- `schemas/`: Pydantic request/response schemas

### Shared Package
`shared/python/pr_review_shared/`: Common encryption utilities and models shared between web-be and scheduler.

## Key Technical Decisions

- **Authentication**: GitHub OAuth 2.0 with stateless JWT sessions
- **Database**: SQLite with Alembic migrations
- **Encryption**: Fernet symmetric encryption for GitHub tokens and PATs
- **Testing**: pytest + httpx (backend), Vitest + React Testing Library (frontend), MSW for API mocking

## Development Workflow

1. Create a new branch from `main`
2. Make changes in small, focused commits
3. Push branch and create pull request using `gh pr create --reviewer copilot-pull-request-reviewer`
4. Merge after review

Always add Copilot as a reviewer when creating PRs for automated code review.

Work in vertical slices following the phases in SPECIFICATION.md.

## Task Tracking

After completing each task:
1. Review `docs/PROJECT-TASKS.md`
2. Verify all deliverables for the task are complete
3. Mark each completed deliverable with `[x]`
4. Confirm acceptance criteria are met
5. Create a pull request for the completed task

Always check the task file at the end of each development phase to ensure all sub-tasks are completed.
