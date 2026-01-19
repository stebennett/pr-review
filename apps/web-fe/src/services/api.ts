import type {
  UserSettings,
  ApiResponse,
  Schedule,
  ScheduleCreate,
  ScheduleUpdate,
  PATOrganization,
  PATRepository,
} from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getAuthToken(): string | null {
  return localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new ApiError(
      response.status,
      errorBody || `HTTP error ${response.status}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  async get<T>(path: string): Promise<T> {
    return request<T>(path, { method: "GET" });
  },

  async post<T>(path: string, data: unknown): Promise<T> {
    return request<T>(path, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async put<T>(path: string, data: unknown): Promise<T> {
    return request<T>(path, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async delete(path: string): Promise<void> {
    return request<void>(path, { method: "DELETE" });
  },
};

// Auth utilities
export function setAuthToken(token: string): void {
  localStorage.setItem("token", token);
}

export function clearAuthToken(): void {
  localStorage.removeItem("token");
}

export function hasAuthToken(): boolean {
  return !!localStorage.getItem("token");
}

// Settings API
interface SettingsData {
  settings: UserSettings;
}

export async function getSettings(): Promise<UserSettings> {
  const response = await api.get<ApiResponse<SettingsData>>("/api/settings");
  return response.data.settings;
}

export async function updateSettings(settings: {
  email: string;
}): Promise<UserSettings> {
  const response = await api.put<ApiResponse<SettingsData>>(
    "/api/settings",
    settings
  );
  return response.data.settings;
}

// Schedules API
interface SchedulesData {
  schedules: Schedule[];
}

interface ScheduleData {
  schedule: Schedule;
}

export async function getSchedules(): Promise<Schedule[]> {
  const response = await api.get<ApiResponse<SchedulesData>>("/api/schedules");
  return response.data.schedules;
}

export async function getSchedule(id: string): Promise<Schedule> {
  const response = await api.get<ApiResponse<ScheduleData>>(
    `/api/schedules/${id}`
  );
  return response.data.schedule;
}

export async function createSchedule(data: ScheduleCreate): Promise<Schedule> {
  const response = await api.post<ApiResponse<ScheduleData>>(
    "/api/schedules",
    data
  );
  return response.data.schedule;
}

export async function updateSchedule(
  id: string,
  data: ScheduleUpdate
): Promise<Schedule> {
  const response = await api.put<ApiResponse<ScheduleData>>(
    `/api/schedules/${id}`,
    data
  );
  return response.data.schedule;
}

export async function deleteSchedule(id: string): Promise<void> {
  await api.delete(`/api/schedules/${id}`);
}

// PAT Preview API
interface PATOrganizationsData {
  organizations: PATOrganization[];
  username: string;
}

interface PATRepositoriesData {
  repositories: PATRepository[];
}

export async function previewPATOrganizations(
  githubPat: string
): Promise<{ organizations: PATOrganization[]; username: string }> {
  const response = await api.post<ApiResponse<PATOrganizationsData>>(
    "/api/schedules/pat/organizations",
    { github_pat: githubPat }
  );
  return {
    organizations: response.data.organizations,
    username: response.data.username,
  };
}

export async function previewPATRepositories(
  githubPat: string,
  organization: string
): Promise<PATRepository[]> {
  const response = await api.post<ApiResponse<PATRepositoriesData>>(
    "/api/schedules/pat/repositories",
    { github_pat: githubPat, organization }
  );
  return response.data.repositories;
}

// Schedule PAT API - uses the schedule's stored PAT
export async function getScheduleOrganizations(
  scheduleId: string
): Promise<{ organizations: PATOrganization[]; username: string }> {
  const response = await api.get<ApiResponse<PATOrganizationsData>>(
    `/api/schedules/${scheduleId}/organizations`
  );
  return {
    organizations: response.data.organizations,
    username: response.data.username,
  };
}

export async function getScheduleRepositories(
  scheduleId: string,
  organization: string
): Promise<PATRepository[]> {
  const response = await api.get<ApiResponse<PATRepositoriesData>>(
    `/api/schedules/${scheduleId}/repositories?organization=${encodeURIComponent(organization)}`
  );
  return response.data.repositories;
}

export { ApiError };
