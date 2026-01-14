import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { useRefresh } from "./useRefresh";
import * as api from "../services/api";
import type { ReactNode } from "react";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    api: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
    ApiError: actual.ApiError,
  };
});

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useRefresh", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns initial state correctly", () => {
    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isRefreshing).toBe(false);
    expect(result.current.rateLimit).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isRateLimited).toBe(false);
    expect(typeof result.current.refresh).toBe("function");
    expect(typeof result.current.clearError).toBe("function");
  });

  it("refreshes successfully and updates rate limit", async () => {
    const mockResponse = {
      data: { message: "Refresh initiated successfully" },
      meta: {
        rate_limit: {
          remaining: 4500,
          reset_at: "2024-01-15T11:00:00Z",
        },
      },
    };

    (api.api.post as Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.refresh();
    });

    expect(api.api.post).toHaveBeenCalledWith("/api/pulls/refresh", {});
    expect(result.current.rateLimit).toEqual({
      remaining: 4500,
      reset_at: "2024-01-15T11:00:00Z",
    });
    expect(result.current.error).toBeNull();
    expect(result.current.isRateLimited).toBe(false);
  });

  it("sets isRefreshing to true during refresh", async () => {
    let resolvePromise: (value: unknown) => void;
    const mockPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    (api.api.post as Mock).mockReturnValue(mockPromise);

    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.refresh();
    });

    await waitFor(() => {
      expect(result.current.isRefreshing).toBe(true);
    });

    await act(async () => {
      resolvePromise!({
        data: { message: "Refresh initiated successfully" },
        meta: { rate_limit: { remaining: 4500, reset_at: "2024-01-15T11:00:00Z" } },
      });
    });

    await waitFor(() => {
      expect(result.current.isRefreshing).toBe(false);
    });
  });

  it("handles rate limit exceeded error (429)", async () => {
    const error = new api.ApiError(429, '{"detail": "GitHub API rate limit exceeded"}');

    (api.api.post as Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.refresh();
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.isRateLimited).toBe(true);
    expect(result.current.error).toContain("rate limit");
  });

  it("handles authentication error (401)", async () => {
    const error = new api.ApiError(401, "Unauthorized");

    (api.api.post as Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.refresh();
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.error).toContain("session has expired");
  });

  it("handles generic API error", async () => {
    const error = new api.ApiError(500, "Internal Server Error");

    (api.api.post as Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.refresh();
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.error).toContain("Failed to refresh");
  });

  it("handles network error", async () => {
    const error = new Error("Network error");

    (api.api.post as Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.refresh();
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.error).toContain("unexpected error");
  });

  it("clears error when clearError is called", async () => {
    const error = new api.ApiError(500, "Internal Server Error");

    (api.api.post as Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useRefresh(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.refresh();
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.error).not.toBeNull();

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.isRateLimited).toBe(false);
  });
});
