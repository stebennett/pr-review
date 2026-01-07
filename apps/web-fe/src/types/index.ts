export interface User {
  id: string;
  username: string;
  email: string | null;
  avatar_url: string | null;
}

export interface LoginResponse {
  url: string;
}

export interface Organization {
  id: string;
  login: string;
  avatar_url: string;
}

export interface Repository {
  id: string;
  name: string;
  full_name: string;
}

export interface Label {
  name: string;
  color: string;
}

export type CheckStatus = "pass" | "fail" | "pending" | "unknown";

export interface PullRequestAuthor {
  username: string;
  avatar_url: string;
}

export interface PullRequest {
  number: number;
  title: string;
  author: PullRequestAuthor;
  labels: Label[];
  checks_status: CheckStatus;
  html_url: string;
  created_at: string;
}

export interface RepositoryRef {
  organization: string;
  repository: string;
}

export interface Schedule {
  id: string;
  name: string;
  cron_expression: string;
  repositories: RepositoryRef[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RateLimitInfo {
  remaining: number;
  reset_at: string;
}

export interface ApiResponse<T> {
  data: T;
  meta?: {
    rate_limit?: RateLimitInfo;
  };
}
