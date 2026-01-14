import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { useRepositories } from "./useRepositories";
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

describe("useRepositories", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches repositories successfully", async () => {
    const mockRepositories = [
      { id: "1", name: "repo-1", full_name: "my-org/repo-1" },
      { id: "2", name: "repo-2", full_name: "my-org/repo-2" },
    ];

    (api.api.get as Mock).mockResolvedValue({
      data: { repositories: mockRepositories },
    });

    const { result } = renderHook(() => useRepositories("my-org"), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockRepositories);
    expect(api.api.get).toHaveBeenCalledWith(
      "/api/organizations/my-org/repositories"
    );
  });

  it("returns empty array when no repositories", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { repositories: [] },
    });

    const { result } = renderHook(() => useRepositories("my-org"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
  });

  it("handles API errors", async () => {
    (api.api.get as Mock).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useRepositories("my-org"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });

  it("does not fetch when org is null", async () => {
    const { result } = renderHook(() => useRepositories(null), {
      wrapper: createWrapper(),
    });

    // Should not be loading since query is disabled
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(api.api.get).not.toHaveBeenCalled();
  });

  it("encodes organization name in URL", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { repositories: [] },
    });

    renderHook(() => useRepositories("my org"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(api.api.get).toHaveBeenCalled();
    });

    expect(api.api.get).toHaveBeenCalledWith(
      "/api/organizations/my%20org/repositories"
    );
  });
});
