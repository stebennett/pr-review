import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from "vitest";
import { AuthProvider } from "./AuthContext";
import { useAuth } from "../hooks/useAuth";
import * as api from "../services/api";

// Mock the api module
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

function TestComponent() {
  const { user, isLoading, isAuthenticated, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="loading">{isLoading ? "loading" : "not-loading"}</div>
      <div data-testid="authenticated">
        {isAuthenticated ? "authenticated" : "not-authenticated"}
      </div>
      <div data-testid="username">{user?.username || "no-user"}</div>
      <button onClick={login}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("initialization", () => {
    it("sets isLoading to true initially and then false", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(false);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Should eventually show not-loading
      await waitFor(() => {
        expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
      });
    });

    it("checks auth on mount when token exists", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(true);
      (api.api.get as Mock).mockResolvedValue(mockUser);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(api.api.get).toHaveBeenCalledWith("/api/auth/me");
      });

      await waitFor(() => {
        expect(screen.getByTestId("username")).toHaveTextContent("testuser");
      });
    });

    it("sets user to null when no token exists", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(false);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });
      expect(api.api.get).not.toHaveBeenCalled();
    });

    it("clears token and sets user to null when auth check fails", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(true);
      const clearTokenSpy = vi.spyOn(api, "clearAuthToken");
      (api.api.get as Mock).mockRejectedValue(new Error("Unauthorized"));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(clearTokenSpy).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });
    });
  });

  describe("login", () => {
    it("calls login endpoint and redirects to OAuth URL", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(false);
      (api.api.get as Mock).mockResolvedValue({
        url: "https://github.com/login/oauth",
      });

      // Mock window.location.href
      const originalLocation = window.location;
      const mockLocation = { ...originalLocation, href: "" };
      Object.defineProperty(window, "location", {
        writable: true,
        value: mockLocation,
      });

      const user = userEvent.setup();

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
      });

      await user.click(screen.getByRole("button", { name: "Login" }));

      await waitFor(() => {
        expect(api.api.get).toHaveBeenCalledWith("/api/auth/login");
      });

      await waitFor(() => {
        expect(mockLocation.href).toBe("https://github.com/login/oauth");
      });

      // Restore window.location
      Object.defineProperty(window, "location", {
        writable: true,
        value: originalLocation,
      });
    });
  });

  describe("logout", () => {
    it("clears token and redirects to login", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(true);
      (api.api.get as Mock).mockResolvedValue(mockUser);
      const clearTokenSpy = vi.spyOn(api, "clearAuthToken");

      // Mock window.location.href
      const originalLocation = window.location;
      const mockLocation = { ...originalLocation, href: "" };
      Object.defineProperty(window, "location", {
        writable: true,
        value: mockLocation,
      });

      const user = userEvent.setup();

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      await user.click(screen.getByRole("button", { name: "Logout" }));

      expect(clearTokenSpy).toHaveBeenCalled();
      expect(mockLocation.href).toBe("/login");

      // Restore window.location
      Object.defineProperty(window, "location", {
        writable: true,
        value: originalLocation,
      });
    });
  });

  describe("checkAuth", () => {
    it("can be called to re-check authentication", async () => {
      vi.spyOn(api, "hasAuthToken").mockReturnValue(true);
      (api.api.get as Mock).mockResolvedValue(mockUser);

      function TestComponentWithCheckAuth() {
        const { checkAuth, user } = useAuth();
        return (
          <div>
            <div data-testid="username">{user?.username || "no-user"}</div>
            <button onClick={checkAuth}>Check Auth</button>
          </div>
        );
      }

      const user = userEvent.setup();

      render(
        <AuthProvider>
          <TestComponentWithCheckAuth />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId("username")).toHaveTextContent("testuser");
      });

      // Clear the mock calls
      (api.api.get as Mock).mockClear();

      // Trigger checkAuth again
      await user.click(screen.getByRole("button", { name: "Check Auth" }));

      await waitFor(() => {
        expect(api.api.get).toHaveBeenCalledWith("/api/auth/me");
      });
    });
  });
});
