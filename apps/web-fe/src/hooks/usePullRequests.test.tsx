import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { usePullRequests } from "./usePullRequests";
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
  };
});

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("usePullRequests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches pull requests successfully", async () => {
    const mockPulls = [
      {
        number: 1,
        title: "Add feature",
        author: { username: "user1", avatar_url: "https://example.com/u1.png" },
        labels: [{ name: "enhancement", color: "84b6eb" }],
        checks_status: "pass",
        html_url: "https://github.com/my-org/repo-1/pull/1",
        created_at: "2024-01-10T08:00:00Z",
      },
    ];

    (api.api.get as Mock).mockResolvedValue({
      data: { pulls: mockPulls },
      meta: { rate_limit: { remaining: 4500, reset_at: "2024-01-15T11:00:00Z" } },
    });

    const { result } = renderHook(() => usePullRequests("my-org", "repo-1"), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.pulls).toEqual(mockPulls);
    expect(result.current.data?.rateLimit).toEqual({
      remaining: 4500,
      reset_at: "2024-01-15T11:00:00Z",
    });
    expect(api.api.get).toHaveBeenCalledWith(
      "/api/organizations/my-org/repositories/repo-1/pulls"
    );
  });

  it("returns empty array when no pull requests", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { pulls: [] },
    });

    const { result } = renderHook(() => usePullRequests("my-org", "repo-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.pulls).toEqual([]);
    expect(result.current.data?.rateLimit).toBeNull();
  });

  it("handles API errors", async () => {
    (api.api.get as Mock).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => usePullRequests("my-org", "repo-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });

  it("does not fetch when org is null", async () => {
    const { result } = renderHook(() => usePullRequests(null, "repo-1"), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(api.api.get).not.toHaveBeenCalled();
  });

  it("does not fetch when repo is null", async () => {
    const { result } = renderHook(() => usePullRequests("my-org", null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(api.api.get).not.toHaveBeenCalled();
  });

  it("encodes org and repo names in URL", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { pulls: [] },
    });

    renderHook(() => usePullRequests("my org", "my repo"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(api.api.get).toHaveBeenCalled();
    });

    expect(api.api.get).toHaveBeenCalledWith(
      "/api/organizations/my%20org/repositories/my%20repo/pulls"
    );
  });
});
