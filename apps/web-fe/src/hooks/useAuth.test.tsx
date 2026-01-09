import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useAuth } from "./useAuth";
import { AuthContext, type AuthContextType } from "../contexts/AuthContext";
import type { ReactNode } from "react";

describe("useAuth", () => {
  it("throws error when used outside AuthProvider", () => {
    // Suppress console.error for this test since we expect an error
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow("useAuth must be used within an AuthProvider");

    consoleSpy.mockRestore();
  });

  it("returns auth context when used within AuthProvider", () => {
    const mockAuthValue: AuthContextType = {
      user: { id: "123", username: "testuser", email: null, avatar_url: null },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    };

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthContext.Provider value={mockAuthValue}>
        {children}
      </AuthContext.Provider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toEqual(mockAuthValue.user);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });

  it("returns isAuthenticated as false when user is null", () => {
    const mockAuthValue: AuthContextType = {
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    };

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthContext.Provider value={mockAuthValue}>
        {children}
      </AuthContext.Provider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
