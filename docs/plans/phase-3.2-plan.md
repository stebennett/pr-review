# Phase 3.2: JWT Service Implementation Plan

## Overview

Phase 3.2 focuses on completing the JWT service implementation. Based on code review, this task is **already largely complete** from Task 3.1. The JWT service, `get_current_user` dependency, and related tests are already implemented. This phase will verify completeness and ensure all acceptance criteria are met.

## Current State Analysis

### Already Implemented (from Task 3.1)
- `apps/web-be/src/pr_review_api/services/jwt.py`:
  - `create_access_token(user_id: str) -> str` - Creates JWT tokens
  - `verify_token(token: str) -> dict` - Verifies and decodes tokens
  - `TokenError` exception class
- `apps/web-be/src/pr_review_api/dependencies.py`:
  - `get_current_user` dependency for protected routes
  - HTTP Bearer security scheme
- `apps/web-be/tests/test_services/test_jwt.py`:
  - Comprehensive unit tests for JWT service

### User Model (also complete)
- `apps/web-be/src/pr_review_api/models/user.py` - SQLAlchemy User model

## Task 3.2 Deliverables Checklist

Per PROJECT-TASKS.md:

| Deliverable | Status | Notes |
|-------------|--------|-------|
| `create_token(user_id: str) -> str` | Done | Implemented as `create_access_token` |
| `verify_token(token: str) -> dict` | Done | Returns payload or raises `TokenError` |
| `get_current_user` dependency | Done | In `dependencies.py` |
| Unit tests | Done | In `test_jwt.py` |

## Verification Tasks

### Task 1: Verify JWT Service Implementation
- [x] Confirm `create_access_token` matches spec (user_id param, returns string)
- [x] Confirm `verify_token` matches spec (returns dict with sub/iat/exp or raises)
- [x] Confirm proper token expiration handling
- [x] Confirm proper signature validation

### Task 2: Verify get_current_user Dependency
- [x] Confirm it extracts token from Authorization header
- [x] Confirm it calls verify_token
- [x] Confirm it looks up user in database
- [x] Confirm proper error handling (401 responses)

### Task 3: Run Existing Tests
- [x] Run `pytest tests/test_services/test_jwt.py` - verify all pass (8/8 passed)
- [x] Run `pytest tests/test_auth.py` - verify auth endpoint tests pass (10/10 passed)
- [x] Verify test coverage is adequate (91% overall, 100% on jwt.py)

### Task 4: Verify Acceptance Criteria
Per PROJECT-TASKS.md:
- [x] Tokens can be created and verified
- [x] Expired tokens raise appropriate exception
- [x] Invalid tokens raise appropriate exception
- [x] `get_current_user` dependency extracts user from Authorization header

## Implementation Steps

1. **Run existing tests** to verify current implementation works
2. **Review test coverage** to ensure all edge cases are tested
3. **Add any missing tests** if gaps are found
4. **Mark Task 3.2 as complete** in PROJECT-TASKS.md

## Files Involved

### Existing Files (verify only)
- `apps/web-be/src/pr_review_api/services/jwt.py`
- `apps/web-be/src/pr_review_api/dependencies.py`
- `apps/web-be/tests/test_services/test_jwt.py`
- `apps/web-be/tests/test_auth.py`

### Files to Update
- `docs/PROJECT-TASKS.md` - Mark deliverables as complete

## Estimated Scope

This is a **verification task** rather than new implementation. The JWT service was implemented as part of Task 3.1 (GitHub OAuth Backend Endpoints). Primary work is:
1. Running tests to confirm functionality
2. Verifying acceptance criteria are met
3. Updating task tracking documentation

## Notes

The JWT service implementation appears complete and well-structured:
- Uses `python-jose` library for JWT operations
- Configurable via `Settings` (secret key, algorithm, expiration)
- Proper timezone-aware datetime handling
- Clean separation between token creation and verification
- `get_current_user` dependency properly integrates with SQLAlchemy User model
