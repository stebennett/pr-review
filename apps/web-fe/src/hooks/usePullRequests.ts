import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import type { PullRequest, RateLimitInfo } from "../types";

interface PullRequestsData {
  pulls: PullRequest[];
}

interface PullRequestsResponse {
  data: PullRequestsData;
  meta?: {
    rate_limit?: RateLimitInfo;
  };
}

export function usePullRequests(org: string | null, repo: string | null) {
  return useQuery({
    queryKey: ["pullRequests", org, repo],
    queryFn: async () => {
      if (!org || !repo) {
        return { pulls: [], rateLimit: null };
      }
      const response = await api.get<PullRequestsResponse>(
        `/api/organizations/${encodeURIComponent(org)}/repositories/${encodeURIComponent(repo)}/pulls`
      );
      return {
        pulls: response.data.pulls,
        rateLimit: response.meta?.rate_limit ?? null,
      };
    },
    enabled: !!org && !!repo,
  });
}
