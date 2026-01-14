import { useState, useCallback } from "react";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { api, ApiError } from "../services/api";
import type { RateLimitInfo } from "../types";

interface RefreshData {
  message: string;
}

interface RefreshMeta {
  rate_limit: RateLimitInfo;
}

interface RefreshResponse {
  data: RefreshData;
  meta: RefreshMeta;
}

interface UseRefreshResult {
  refresh: () => Promise<void>;
  isRefreshing: boolean;
  rateLimit: RateLimitInfo | null;
  error: string | null;
  isRateLimited: boolean;
  clearError: () => void;
}

export function useRefresh(): UseRefreshResult {
  const queryClient = useQueryClient();
  const [rateLimit, setRateLimit] = useState<RateLimitInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRateLimited, setIsRateLimited] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<RefreshResponse>("/api/pulls/refresh", {});
      return response;
    },
    onSuccess: async (response) => {
      setRateLimit(response.meta.rate_limit);
      setError(null);
      setIsRateLimited(false);

      // Invalidate all PR-related queries to trigger refetch
      await queryClient.invalidateQueries({ queryKey: ["organizations"] });
      await queryClient.invalidateQueries({ queryKey: ["repositories"] });
      await queryClient.invalidateQueries({ queryKey: ["pullRequests"] });
    },
    onError: (err: Error) => {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setIsRateLimited(true);
          // Try to parse the error body for reset time
          try {
            const errorData = JSON.parse(err.message);
            setError(
              errorData.detail || "GitHub API rate limit exceeded. Please try again later."
            );
          } catch {
            setError("GitHub API rate limit exceeded. Please try again later.");
          }
        } else if (err.status === 401) {
          setError("Your session has expired. Please log in again.");
        } else {
          setError("Failed to refresh data. Please try again.");
        }
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    },
  });

  const refresh = useCallback(async () => {
    await mutation.mutateAsync();
  }, [mutation]);

  const clearError = useCallback(() => {
    setError(null);
    setIsRateLimited(false);
  }, []);

  return {
    refresh,
    isRefreshing: mutation.isPending,
    rateLimit,
    error,
    isRateLimited,
    clearError,
  };
}
