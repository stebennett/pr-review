import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import Dashboard from "./Dashboard";
import { AuthContext, type AuthContextType } from "../contexts/AuthContext";
import * as api from "../services/api";

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

const mockUser = {
  id: "123",
  username: "testuser",
  email: "test@example.com",
  avatar_url: "https://example.com/avatar.png",
};

const mockOrganizations = [
  { id: "1", login: "org-one", avatar_url: "https://example.com/org1.png" },
  { id: "2", login: "org-two", avatar_url: "https://example.com/org2.png" },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const authValue: AuthContextType = {
    user: mockUser,
    isLoading: false,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
  };

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
    </QueryClientProvider>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("shows loading state while fetching organizations", () => {
    // Return a promise that never resolves to keep loading state
    (api.api.get as Mock).mockReturnValue(new Promise(() => {}));

    render(<Dashboard />, { wrapper: createWrapper() });

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("displays organizations after loading", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("org-one")).toBeInTheDocument();
    });
  });

  it("shows error message when fetch fails", async () => {
    (api.api.get as Mock).mockRejectedValue(new Error("Network error"));

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByText("Failed to load organizations. Please try again.")
      ).toBeInTheDocument();
    });
  });

  it("selects first organization by default", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Repositories in org-one")).toBeInTheDocument();
    });
  });

  it("persists selected organization to localStorage", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("org-one")).toBeInTheDocument();
    });

    // Open dropdown and select second org
    const dropdownButton = screen.getByRole("button", { expanded: false });
    await user.click(dropdownButton);

    await user.click(screen.getByText("org-two"));

    expect(localStorage.getItem("pr-review-selected-org")).toBe("org-two");
  });

  it("restores selected organization from localStorage", async () => {
    localStorage.setItem("pr-review-selected-org", "org-two");

    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Repositories in org-two")).toBeInTheDocument();
    });
  });

  it("falls back to first org if stored org not found", async () => {
    localStorage.setItem("pr-review-selected-org", "non-existent-org");

    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Repositories in org-one")).toBeInTheDocument();
    });
  });

  it("shows placeholder for repository list", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByText("Repository list will be displayed here.")
      ).toBeInTheDocument();
    });
  });

  it("renders navbar with user info", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { organizations: mockOrganizations },
    });

    render(<Dashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("PR Review")).toBeInTheDocument();
      expect(screen.getByText("testuser")).toBeInTheDocument();
      expect(screen.getByText("Sign out")).toBeInTheDocument();
    });
  });
});
