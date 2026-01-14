import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from "vitest";
import App from "./App";
import * as api from "./services/api";

// Mock the api module
vi.mock("./services/api", async () => {
  const actual = await vi.importActual("./services/api");
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

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderApp(initialEntries: string[] = ["/"]) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("when not authenticated", () => {
    beforeEach(() => {
      // No token in localStorage
      vi.spyOn(api, "hasAuthToken").mockReturnValue(false);
    });

    it("redirects to login page when accessing protected route", async () => {
      renderApp(["/"]);

      await waitFor(() => {
        expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
      });
    });

    it("renders login page at /login route", async () => {
      renderApp(["/login"]);

      await waitFor(() => {
        expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
      });
      expect(
        screen.getByRole("button", { name: /sign in with github/i })
      ).toBeInTheDocument();
    });
  });

  describe("when authenticated", () => {
    beforeEach(() => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(true);
      // Mock /api/auth/me for user info
      (api.api.get as Mock).mockImplementation((path: string) => {
        if (path === "/api/auth/me") {
          return Promise.resolve(mockUser);
        }
        if (path === "/api/organizations") {
          return Promise.resolve({ data: { organizations: mockOrganizations } });
        }
        return Promise.reject(new Error(`Unexpected path: ${path}`));
      });
    });

    it("renders the dashboard with user info", async () => {
      renderApp(["/"]);

      await waitFor(() => {
        expect(screen.getByText("PR Review")).toBeInTheDocument();
      });
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });

    it("displays user avatar when available", async () => {
      renderApp(["/"]);

      await waitFor(() => {
        const avatar = screen.getByAltText("testuser");
        expect(avatar).toBeInTheDocument();
        expect(avatar).toHaveAttribute("src", mockUser.avatar_url);
      });
    });

    it("shows sign out button", async () => {
      renderApp(["/"]);

      await waitFor(() => {
        expect(screen.getByText("Sign out")).toBeInTheDocument();
      });
    });

    it("redirects authenticated user from login to dashboard", async () => {
      renderApp(["/login"]);

      await waitFor(() => {
        expect(screen.getByText("PR Review")).toBeInTheDocument();
      });
    });

    it("loads and displays organizations", async () => {
      renderApp(["/"]);

      await waitFor(() => {
        expect(screen.getByText("org-one")).toBeInTheDocument();
      });
    });

    it("shows repository placeholder for selected organization", async () => {
      renderApp(["/"]);

      await waitFor(() => {
        expect(screen.getByText("Repositories in org-one")).toBeInTheDocument();
      });
    });
  });

  describe("OAuth callback", () => {
    it("stores token from URL and removes it from query params", async () => {
      const setTokenSpy = vi.spyOn(api, "setAuthToken");
      vi.spyOn(api, "hasAuthToken").mockReturnValue(false);
      (api.api.get as Mock).mockResolvedValue(mockUser);

      renderApp(["/?token=test-jwt-token"]);

      await waitFor(() => {
        expect(setTokenSpy).toHaveBeenCalledWith("test-jwt-token");
      });
    });
  });

  describe("auth error handling", () => {
    it("redirects to login when auth check fails", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(true);
      (api.api.get as Mock).mockRejectedValue(new Error("Unauthorized"));

      renderApp(["/"]);

      await waitFor(() => {
        expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
      });
    });
  });
});
