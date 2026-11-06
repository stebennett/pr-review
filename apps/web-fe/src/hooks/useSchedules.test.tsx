import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useSchedules, useSchedule } from "./useSchedules";
import * as api from "../services/api";
import type { ReactNode } from "react";
import type { Schedule, ScheduleCreate, ScheduleUpdate } from "../types";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    getSchedules: vi.fn(),
    getSchedule: vi.fn(),
    createSchedule: vi.fn(),
    updateSchedule: vi.fn(),
    deleteSchedule: vi.fn(),
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

const mockSchedule: Schedule = {
  id: "schedule-1",
  name: "Daily PR Check",
  cron_expression: "0 9 * * 1-5",
  repositories: [
    { organization: "test-org", repository: "test-repo" },
  ],
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockSchedule2: Schedule = {
  id: "schedule-2",
  name: "Weekly Summary",
  cron_expression: "0 9 * * 1",
  repositories: [
    { organization: "test-org", repository: "another-repo" },
  ],
  is_active: false,
  created_at: "2024-01-02T00:00:00Z",
  updated_at: "2024-01-02T00:00:00Z",
};

describe("useSchedules", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches schedules successfully", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([mockSchedule, mockSchedule2]);

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.schedules).toEqual([mockSchedule, mockSchedule2]);
    expect(api.getSchedules).toHaveBeenCalled();
  });

  it("returns empty array when no schedules", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([]);

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.schedules).toEqual([]);
  });

  it("handles fetch errors", async () => {
    vi.mocked(api.getSchedules).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });

  it("creates schedule successfully", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([]);
    vi.mocked(api.createSchedule).mockResolvedValue(mockSchedule);

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const newSchedule: ScheduleCreate = {
      name: "Daily PR Check",
      cron_expression: "0 9 * * 1-5",
      github_pat: "ghp_test123",
      repositories: [{ organization: "test-org", repository: "test-repo" }],
      is_active: true,
    };

    await act(async () => {
      await result.current.createSchedule(newSchedule);
    });

    expect(api.createSchedule).toHaveBeenCalledWith(newSchedule);
  });

  it("handles create errors", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([]);
    vi.mocked(api.createSchedule).mockRejectedValue(new Error("Create failed"));

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const newSchedule: ScheduleCreate = {
      name: "Test",
      cron_expression: "0 9 * * *",
      github_pat: "ghp_test",
      repositories: [{ organization: "org", repository: "repo" }],
      is_active: true,
    };

    await expect(result.current.createSchedule(newSchedule)).rejects.toThrow(
      "Create failed"
    );
  });

  it("shows creating state during mutation", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([]);

    let resolveCreate: (value: Schedule) => void;
    const pendingPromise = new Promise<Schedule>((resolve) => {
      resolveCreate = resolve;
    });
    vi.mocked(api.createSchedule).mockReturnValue(pendingPromise);

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const newSchedule: ScheduleCreate = {
      name: "Test",
      cron_expression: "0 9 * * *",
      github_pat: "ghp_test",
      repositories: [{ organization: "org", repository: "repo" }],
      is_active: true,
    };

    act(() => {
      result.current.createSchedule(newSchedule).catch(() => {});
    });

    await waitFor(() => {
      expect(result.current.isCreating).toBe(true);
    });

    await act(async () => {
      resolveCreate!(mockSchedule);
    });

    await waitFor(() => {
      expect(result.current.isCreating).toBe(false);
    });
  });

  it("updates schedule successfully", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([mockSchedule]);
    vi.mocked(api.updateSchedule).mockResolvedValue({
      ...mockSchedule,
      name: "Updated Name",
    });

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const updateData: ScheduleUpdate = { name: "Updated Name" };

    await act(async () => {
      await result.current.updateSchedule("schedule-1", updateData);
    });

    expect(api.updateSchedule).toHaveBeenCalledWith("schedule-1", updateData);
  });

  it("handles update errors", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([mockSchedule]);
    vi.mocked(api.updateSchedule).mockRejectedValue(new Error("Update failed"));

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(
      result.current.updateSchedule("schedule-1", { name: "New Name" })
    ).rejects.toThrow("Update failed");
  });

  it("deletes schedule successfully", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([mockSchedule]);
    vi.mocked(api.deleteSchedule).mockResolvedValue(undefined);

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.deleteSchedule("schedule-1");
    });

    expect(api.deleteSchedule).toHaveBeenCalledWith("schedule-1");
  });

  it("handles delete errors", async () => {
    vi.mocked(api.getSchedules).mockResolvedValue([mockSchedule]);
    vi.mocked(api.deleteSchedule).mockRejectedValue(new Error("Delete failed"));

    const { result } = renderHook(() => useSchedules(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(
      result.current.deleteSchedule("schedule-1")
    ).rejects.toThrow("Delete failed");
  });
});

describe("useSchedule", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches single schedule successfully", async () => {
    vi.mocked(api.getSchedule).mockResolvedValue(mockSchedule);

    const { result } = renderHook(() => useSchedule("schedule-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockSchedule);
    expect(api.getSchedule).toHaveBeenCalledWith("schedule-1");
  });

  it("does not fetch when id is null", async () => {
    const { result } = renderHook(() => useSchedule(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(api.getSchedule).not.toHaveBeenCalled();
  });

  it("handles fetch errors", async () => {
    vi.mocked(api.getSchedule).mockRejectedValue(new Error("Not found"));

    const { result } = renderHook(() => useSchedule("invalid-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });
});
