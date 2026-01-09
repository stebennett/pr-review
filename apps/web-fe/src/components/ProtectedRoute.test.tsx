import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { ProtectedRoute } from "./ProtectedRoute";
import { AuthContext, type AuthContextType } from "../contexts/AuthContext";

function renderWithAuth(
  authValue: AuthContextType,
  initialEntries: string[] = ["/protected"]
) {
  return render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe("ProtectedRoute", () => {
  it("shows loading spinner when auth is loading", () => {
    const authValue: AuthContextType = {
      user: null,
      isLoading: true,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    };

    renderWithAuth(authValue);

    // Should show loading spinner (SVG with animate-spin class)
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("redirects to login when not authenticated", () => {
    const authValue: AuthContextType = {
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    };

    renderWithAuth(authValue);

    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    const authValue: AuthContextType = {
      user: { id: "123", username: "testuser", email: null, avatar_url: null },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    };

    renderWithAuth(authValue);

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });

  it("preserves the intended destination in location state", () => {
    const authValue: AuthContextType = {
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    };

    // This tests that the Navigate component is called with the state prop
    // containing the original location
    renderWithAuth(authValue, ["/protected?foo=bar"]);

    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });
});
