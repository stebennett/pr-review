import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useSettings } from "./useSettings";
import * as api from "../services/api";
import type { ReactNode } from "react";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
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

describe("useSettings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches settings successfully", async () => {
    const mockSettings = { email: "test@example.com" };
    vi.mocked(api.getSettings).mockResolvedValue(mockSettings);

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.settings).toEqual(mockSettings);
    expect(api.getSettings).toHaveBeenCalled();
  });

  it("handles null email in settings", async () => {
    const mockSettings = { email: null };
    vi.mocked(api.getSettings).mockResolvedValue(mockSettings);

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.settings).toEqual(mockSettings);
  });

  it("handles fetch errors", async () => {
    vi.mocked(api.getSettings).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });

  it("updates settings successfully", async () => {
    const mockSettings = { email: "old@example.com" };
    const updatedSettings = { email: "new@example.com" };

    vi.mocked(api.getSettings).mockResolvedValue(mockSettings);
    vi.mocked(api.updateSettings).mockResolvedValue(updatedSettings);

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.updateSettings({ email: "new@example.com" });
    });

    await waitFor(() => {
      expect(result.current.updateSuccess).toBe(true);
    });

    expect(api.updateSettings).toHaveBeenCalledWith({ email: "new@example.com" });
    expect(result.current.settings).toEqual(updatedSettings);
  });

  it("handles update errors", async () => {
    const mockSettings = { email: "test@example.com" };
    vi.mocked(api.getSettings).mockResolvedValue(mockSettings);
    vi.mocked(api.updateSettings).mockRejectedValue(new Error("Update failed"));

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.updateSettings({ email: "new@example.com" });
    });

    await waitFor(() => {
      expect(result.current.updateError).toBeTruthy();
    });

    expect(result.current.updateSuccess).toBe(false);
  });

  it("shows updating state during mutation", async () => {
    const mockSettings = { email: "test@example.com" };
    vi.mocked(api.getSettings).mockResolvedValue(mockSettings);

    let resolveUpdate: (value: { email: string }) => void;
    const pendingPromise = new Promise<{ email: string }>((resolve) => {
      resolveUpdate = resolve;
    });
    vi.mocked(api.updateSettings).mockReturnValue(pendingPromise);

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.updateSettings({ email: "new@example.com" });
    });

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(true);
    });

    act(() => {
      resolveUpdate!({ email: "new@example.com" });
    });

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(false);
    });
  });

  it("can reset update state", async () => {
    const mockSettings = { email: "test@example.com" };
    const updatedSettings = { email: "new@example.com" };

    vi.mocked(api.getSettings).mockResolvedValue(mockSettings);
    vi.mocked(api.updateSettings).mockResolvedValue(updatedSettings);

    const { result } = renderHook(() => useSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.updateSettings({ email: "new@example.com" });
    });

    await waitFor(() => {
      expect(result.current.updateSuccess).toBe(true);
    });

    act(() => {
      result.current.resetUpdate();
    });

    await waitFor(() => {
      expect(result.current.updateSuccess).toBe(false);
    });
  });
});
