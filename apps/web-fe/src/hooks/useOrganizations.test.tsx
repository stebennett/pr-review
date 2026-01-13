import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { useOrganizations } from "./useOrganizations";
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

describe("useOrganizations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches organizations successfully", async () => {
    const mockOrganizations = [
      { id: "1", login: "org-1", avatar_url: "https://example.com/org1.png" },
      { id: "2", login: "org-2", avatar_url: "https://example.com/org2.png" },
    ];

    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    const { result } = renderHook(() => useOrganizations(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockOrganizations);
    expect(api.api.get).toHaveBeenCalledWith("/api/organizations");
  });

  it("returns empty array when no organizations", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: [] },
    });

    const { result } = renderHook(() => useOrganizations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual([]);
  });

  it("handles API errors", async () => {
    (api.api.get as Mock).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useOrganizations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });
});
