# Phase 4.6: Build Repository List Component

## Overview

Create the RepoList component that displays repositories and their pull requests for the selected organization. This includes a custom hook for fetching PR data and proper loading/empty states.

## Deliverables

Based on Task 4.6 from PROJECT-TASKS.md:

- [x] Create RepoList component
- [x] Create usePullRequests hook to fetch PRs for selected org
- [x] Display repositories as collapsible sections
- [x] Show PR count badge for each repository
- [x] Handle loading and empty states
- [x] Write component tests

## Implementation Plan

### 1. Create Types for Repository and Pull Request Data

**File:** `apps/web-fe/src/types/index.ts`

Add TypeScript interfaces for:
- `Repository` - id, name, full_name
- `PullRequest` - number, title, author, labels, checks_status, html_url, created_at
- `Author` - username, avatar_url
- `Label` - name, color

### 2. Create usePullRequests Hook

**File:** `apps/web-fe/src/hooks/usePullRequests.ts`

The hook will:
- Accept an organization name as parameter
- Fetch repositories for the organization
- For each repository, fetch open pull requests
- Return repositories with their PRs, loading state, and error state
- Use React Query for data fetching and caching

### 3. Create RepoList Component

**File:** `apps/web-fe/src/components/RepoList.tsx`

Component features:
- Accept organization as prop
- Display repositories in collapsible accordion-style sections
- Show PR count badge next to each repository name
- Expand/collapse on click
- Only fetch PRs for expanded repositories (optimization)

Layout:
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

### 4. Create useRepositories Hook

**File:** `apps/web-fe/src/hooks/useRepositories.ts`

Separate hook for fetching just repositories:
- Fetch repositories for an organization
- Used by RepoList to get the list of repos
- PRs fetched separately per repo when expanded

### 5. Handle Loading and Empty States

- Show skeleton/spinner while loading repositories
- Show "No repositories found" when organization has no repos
- Show "No open pull requests" when repo has no PRs
- Handle error states with retry option

### 6. Write Tests

**Files:**
- `apps/web-fe/src/components/RepoList.test.tsx`
- `apps/web-fe/src/hooks/usePullRequests.test.tsx`
- `apps/web-fe/src/hooks/useRepositories.test.tsx`

Test cases:
- RepoList renders repositories correctly
- Repositories expand/collapse on click
- PR count badges display correct numbers
- Loading states shown while fetching
- Empty states displayed appropriately
- Error handling works correctly

### 7. Integrate with Dashboard

**File:** `apps/web-fe/src/pages/Dashboard.tsx`

- Add RepoList component to Dashboard
- Pass selected organization to RepoList
- Handle case when no organization is selected

## Task Sequence

1. **Add types** - Define TypeScript interfaces
2. **Create useRepositories hook** - Fetch repositories for an org
3. **Create usePullRequests hook** - Fetch PRs for a repository
4. **Create RepoList component** - Main component with collapsible sections
5. **Integrate with Dashboard** - Wire up the component
6. **Add tests** - Write comprehensive tests
7. **Update PROJECT-TASKS.md** - Mark deliverables complete

## API Endpoints Used

- `GET /api/organizations/{org}/repositories` - List repositories
- `GET /api/organizations/{org}/repositories/{repo}/pulls` - List PRs for a repo

## Dependencies

- Task 4.5 (Dashboard with org selector) - ✅ Completed
- Task 4.3 (Repositories endpoint) - ✅ Completed
- Task 4.4 (Pull requests endpoint) - ✅ Completed

## Acceptance Criteria

- Repositories are displayed for selected organization
- Each repository shows count of open PRs
- Clicking repository expands/collapses PR list
- Loading spinner shown while fetching
- Empty and error states handled gracefully
