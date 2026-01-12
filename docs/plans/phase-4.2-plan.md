# Phase 4.2 Implementation Plan: Organizations Endpoint

## Overview

Implement the `GET /api/organizations` endpoint that returns organizations the authenticated user has access to via GitHub.

## Task 4.2 Requirements

From PROJECT-TASKS.md:
- Implement `GET /api/organizations`
- Return list of organizations with id, name, and avatar_url
- Require authentication
- Write endpoint tests

## Implementation Steps

### 1. Create Organizations Router

**File:** `apps/web-be/src/pr_review_api/routers/organizations.py`

- Create new router module
- Implement `GET /api/organizations` endpoint
- Use `get_current_user` dependency for authentication
- Call GitHub service to fetch user organizations
- Return formatted response matching specification

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

### 2. Create Response Schemas

**File:** `apps/web-be/src/pr_review_api/schemas/organization.py`

- Review existing `Organization` schema (already created in Task 4.1)
- Create `OrganizationsResponse` wrapper schema for API response format
- Ensure schema matches the specification response format

### 3. Register Router in Main App

**File:** `apps/web-be/src/pr_review_api/main.py`

- Import organizations router
- Add router with `/api/organizations` prefix

### 4. Write Endpoint Tests

**File:** `apps/web-be/tests/test_organizations.py`

- Test successful organization list retrieval
- Test authentication required (401 without token)
- Test with mocked GitHub API responses
- Test empty organization list
- Test error handling for GitHub API failures

## Dependencies

- Task 4.1 (GitHub API Service) - **COMPLETED**
  - `GitHubAPIService.get_user_organizations()` already implemented
  - `Organization` Pydantic schema already created
- Task 3.2 (JWT Service) - **COMPLETED**
  - `get_current_user` dependency available
- Task 3.3 (User Model) - **COMPLETED**
  - User model with `github_access_token` field

## Files to Create/Modify

| File | Action |
|------|--------|
| `apps/web-be/src/pr_review_api/routers/organizations.py` | Create |
| `apps/web-be/src/pr_review_api/routers/__init__.py` | Modify (export) |
| `apps/web-be/src/pr_review_api/schemas/organization.py` | Modify (add response wrapper) |
| `apps/web-be/src/pr_review_api/main.py` | Modify (register router) |
| `apps/web-be/tests/test_organizations.py` | Create |

## Acceptance Criteria

- [ ] Endpoint requires authentication (returns 401 without valid JWT)
- [ ] Returns organizations from GitHub API
- [ ] Response format matches specification
- [ ] Tests verify response format
- [ ] Tests cover error cases

## Testing Commands

```bash
cd apps/web-be
pytest tests/test_organizations.py -v
ruff check .
ruff format .
```
