import type { UserSettings, ApiResponse } from "../types";

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

export { ApiError };
