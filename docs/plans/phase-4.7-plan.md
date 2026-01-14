# Phase 4.7: Build Pull Request Card Component

## Overview

Create the PullRequestCard component that displays individual pull request details within the repository list. This component is a child of the RepoList component created in Task 4.6.

## Task Summary

From the specification (Task 4.7):
- Create PullRequestCard component
- Display title as clickable link (opens GitHub in new tab)
- Display colored label badges
- Display author avatar and username
- Display checks status icon (✓ green / ✗ red / ● yellow)
- Display relative time (e.g., "3 days ago") using date-fns
- Write component tests

## Deliverables

### 1. PullRequestCard Component
**File:** `apps/web-fe/src/components/PullRequestCard.tsx`

Component requirements:
- Accept a `PullRequest` prop with all PR data
- Display PR title as a link that opens the GitHub PR in a new tab
- Render colored label badges matching GitHub's label colors
- Show author avatar (small circular image) and username
- Display checks status with appropriate icon and color:
  - `pass` → ✓ green checkmark
  - `fail` → ✗ red X
  - `pending` → ● yellow circle
- Show relative time since PR was created using date-fns `formatDistanceToNow`

### 2. Date Utility Updates
**File:** `apps/web-fe/src/utils/date.ts`

Add helper function for formatting relative time:
- `formatRelativeTime(date: string | Date): string` - Returns "X days ago" format

### 3. Component Tests
**File:** `apps/web-fe/tests/components/PullRequestCard.test.tsx`

Test coverage for:
- Rendering all PR fields correctly
- Title links to correct GitHub URL with target="_blank"
- Labels display with correct colors
- Different checks status icons render correctly
- Relative time displays correctly
- Author avatar and username display

## Component Design

```
┌─────────────────────────────────────────────────────────────┐
│  ✓  Add authentication feature                    3 days ago│
│     [enhancement] [high-priority]                           │
│     👤 octocat                                              │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Update date utility
- Add `formatRelativeTime` function using date-fns `formatDistanceToNow`

### Step 2: Create PullRequestCard component
- Create base component structure with TypeScript props interface
- Implement title as external link with `target="_blank"` and `rel="noopener noreferrer"`
- Add checks status icon with appropriate styling
- Add relative time display
- Implement label badges with dynamic background colors
- Add author section with avatar and username

### Step 3: Style the component
- Use Tailwind CSS for styling
- Ensure proper spacing and layout
- Make labels visually match GitHub's style
- Add hover states for interactive elements

### Step 4: Write tests
- Test component renders with mock PR data
- Test all visual elements are present
- Test link has correct attributes
- Test different checks status values
- Test label color rendering

### Step 5: Integration
- Ensure component integrates with RepoList from Task 4.6
- Verify TypeScript types align with existing PullRequest type

## Type Definitions

The PullRequest type should already exist from Task 4.4. Expected shape:
```typescript
interface PullRequest {
  number: number;
  title: string;
  author: {
    username: string;
    avatar_url: string;
  };
  labels: Array<{
    name: string;
    color: string;
  }>;
  checks_status: 'pass' | 'fail' | 'pending';
  html_url: string;
  created_at: string;
}
```

## Acceptance Criteria

- [ ] All PR fields displayed correctly
- [ ] Title links to GitHub PR page
- [ ] Labels rendered with correct colors
- [ ] Check status icon reflects pass/fail/pending
- [ ] Dates formatted as relative time
- [ ] Component tests pass with good coverage

## Dependencies

- Task 4.6 (RepoList component) - provides parent component context
- Task 4.4 (Pull requests endpoint) - provides PullRequest type definition
- date-fns library (already installed)
