# Phase 4.8: Manual Refresh Functionality

## Overview

This phase implements the manual refresh feature allowing users to re-fetch PR data from GitHub. The refresh button in the navbar will trigger a refetch of all cached data, display loading states, and show rate limit information.

## Current State

- The `Navbar` component has a placeholder refresh button (non-functional)
- The `usePullRequests` hook uses React Query for data fetching with caching
- Rate limit info is already returned from the `/api/organizations/{org}/repositories/{repo}/pulls` endpoint

## Implementation Tasks

### Task 4.8.1: Add Backend Refresh Endpoint

**Files to modify:**
- `apps/web-be/src/pr_review_api/routers/pulls.py`
- `apps/web-be/src/pr_review_api/main.py` (if router not already registered)

**Implementation:**
- Add `POST /api/pulls/refresh` endpoint
- Return current rate limit information
- No additional server-side caching needed - React Query handles client-side caching
- The endpoint primarily serves to validate user can still access GitHub and return rate limit status

**Endpoint response:**
```json
{
  "data": {
    "message": "Refresh initiated successfully"
  },
  "meta": {
    "rate_limit": {
      "remaining": 4500,
      "reset_at": "2024-01-15T11:00:00Z"
    }
  }
}
```

### Task 4.8.2: Create useRefresh Hook

**Files to create:**
- `apps/web-fe/src/hooks/useRefresh.ts`

**Implementation:**
- Create a hook that invalidates React Query cache for repositories and pull requests
- Track refresh loading state
- Store and expose rate limit information
- Use `useQueryClient().invalidateQueries()` to trigger refetch

### Task 4.8.3: Update Navbar Component

**Files to modify:**
- `apps/web-fe/src/components/Navbar.tsx`

**Implementation:**
- Add `onRefresh` callback prop
- Add `isRefreshing` prop for loading state
- Add `rateLimit` prop to display rate limit info
- Show spinning animation on refresh button when refreshing
- Display rate limit tooltip/info after refresh

### Task 4.8.4: Update Dashboard to Handle Refresh

**Files to modify:**
- `apps/web-fe/src/pages/Dashboard.tsx`

**Implementation:**
- Use the new `useRefresh` hook
- Pass refresh handler and state to Navbar
- Optionally show rate limit status in UI after refresh

### Task 4.8.5: Add Rate Limit Exceeded Handling

**Files to modify:**
- `apps/web-fe/src/components/Navbar.tsx`
- `apps/web-fe/src/hooks/useRefresh.ts`

**Implementation:**
- Detect rate limit exceeded errors (HTTP 403 or remaining=0)
- Display user-friendly message with reset time
- Disable refresh button temporarily when rate limited

### Task 4.8.6: Write Tests

**Files to create/modify:**
- `apps/web-be/tests/test_pulls.py` (add refresh endpoint tests)
- `apps/web-fe/src/hooks/useRefresh.test.tsx`
- `apps/web-fe/src/components/Navbar.test.tsx` (update with refresh tests)
- `apps/web-fe/src/pages/Dashboard.test.tsx` (update with refresh tests)

**Test coverage:**
- Backend: refresh endpoint returns rate limit info
- Backend: refresh endpoint handles rate limit exceeded
- Frontend: refresh button triggers cache invalidation
- Frontend: loading state displayed during refresh
- Frontend: rate limit info displayed after refresh
- Frontend: rate limit exceeded shows error message

## Acceptance Criteria

1. Clicking refresh button re-fetches data from GitHub
2. Loading indicator shown during refresh (spinning icon on button)
3. Rate limit info displayed after refresh (e.g., "4500 requests remaining, resets in 45 min")
4. User notified if rate limit exceeded with reset time
5. All tests pass

## Technical Notes

- React Query's `invalidateQueries` will automatically refetch active queries
- The backend refresh endpoint is lightweight - it just validates token and returns rate limit
- Rate limit info comes from GitHub's response headers (already implemented in GitHub service)
- Consider showing rate limit as a tooltip on hover or a small badge near refresh button

## Dependencies

- Task 4.7 (PullRequestCard) - Completed
- Task 4.6 (RepoList) - Completed
- Task 4.5 (Dashboard with OrgSelector) - Completed
