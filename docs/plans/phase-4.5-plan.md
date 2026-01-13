# Phase 4.5 Implementation Plan: Dashboard Page with Organization Selector

## Overview

Task 4.5 builds the main dashboard page with navbar and organization selector dropdown. This is a frontend-only task that connects to the backend APIs implemented in phases 4.2-4.4.

## Deliverables

From PROJECT-TASKS.md:
- [ ] Create Dashboard page component
- [ ] Create Navbar component with user avatar and logout
- [ ] Create OrgSelector dropdown component
- [ ] Implement `useOrganizations` hook to fetch organizations
- [ ] Store selected organization in state (and localStorage for persistence)
- [ ] Write component tests

## Implementation Tasks

### 1. Create useOrganizations Hook
**File:** `apps/web-fe/src/hooks/useOrganizations.ts`

- Use React Query to fetch organizations from `GET /api/organizations`
- Handle loading, error, and success states
- Return organizations array plus query state

### 2. Create OrgSelector Component
**File:** `apps/web-fe/src/components/OrgSelector.tsx`

- Dropdown component showing user's organizations
- Display org avatar and login name
- Handle selection changes
- Show loading state while fetching
- Pass selected org up via callback

### 3. Create Navbar Component
**File:** `apps/web-fe/src/components/Navbar.tsx`

- Contains OrgSelector on the left
- Placeholder for Refresh button (Task 4.8)
- User avatar and logout button on the right
- Use auth context for user info and logout

### 4. Create Dashboard Page
**File:** `apps/web-fe/src/pages/Dashboard.tsx`

- Main page layout with Navbar
- Manage selected organization state
- Persist selected org to localStorage
- Restore selection on mount
- Placeholder area for repository list (Task 4.6)

### 5. Update App Routes
**File:** `apps/web-fe/src/App.tsx`

- Add Dashboard route at `/`
- Ensure route is protected (requires auth)

### 6. Write Component Tests

**Test files:**
- `apps/web-fe/src/hooks/useOrganizations.test.ts`
- `apps/web-fe/src/components/OrgSelector.test.tsx`
- `apps/web-fe/src/components/Navbar.test.tsx`
- `apps/web-fe/src/pages/Dashboard.test.tsx`

Test coverage:
- Hook fetches and returns organizations
- OrgSelector renders orgs and handles selection
- Navbar renders correctly with user info
- Dashboard persists selection to localStorage
- Loading and error states handled

## Technical Details

### Dashboard Layout (from spec)
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

### Organization API Response
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

### State Management
- Selected org stored in Dashboard component state
- Persisted to localStorage key: `pr-review-selected-org`
- On mount, check localStorage and validate org still exists

## Dependencies

- Backend API: `GET /api/organizations` (Task 4.2 - completed)
- Auth context and useAuth hook (Task 3.5 - completed)
- React Query already configured

## Acceptance Criteria

- Dashboard displays after login
- Organization dropdown loads and shows user's orgs
- Selecting an org updates state
- Selected org persists on page refresh
