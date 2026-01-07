import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import Login from "./Login";
import * as api from "../services/api";

function renderLogin(initialEntries: string[] = ["/login"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Login />
    </MemoryRouter>
  );
}

describe("Login", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the login page with title and description", () => {
    renderLogin();

    expect(screen.getByText("PR Review")).toBeInTheDocument();
    expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
    expect(
      screen.getByText("Monitor pull requests across your GitHub organizations")
    ).toBeInTheDocument();
  });

  it("renders the GitHub login button", () => {
    renderLogin();

    const button = screen.getByRole("button", { name: /sign in with github/i });
    expect(button).toBeInTheDocument();
  });

  it("displays error message when OAuth fails", () => {
    render(
      <MemoryRouter initialEntries={["/login?error=oauth_failed"]}>
        <Login />
      </MemoryRouter>
    );

    expect(
      screen.getByText("Authentication failed. Please try again.")
    ).toBeInTheDocument();
  });

  it("initiates OAuth flow when login button is clicked", async () => {
    const user = userEvent.setup();
    const mockGet = vi.spyOn(api.api, "get").mockResolvedValue({
      url: "https://github.com/login/oauth/authorize?client_id=test",
    });

    // Mock window.location.href
    const originalLocation = window.location;
    const mockLocation = { ...originalLocation, href: "" };
    Object.defineProperty(window, "location", {
      writable: true,
      value: mockLocation,
    });

    renderLogin();

    const button = screen.getByRole("button", { name: /sign in with github/i });
    await user.click(button);

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith("/api/auth/login");
    });

    await waitFor(() => {
      expect(mockLocation.href).toBe(
        "https://github.com/login/oauth/authorize?client_id=test"
      );
    });

    // Restore window.location
    Object.defineProperty(window, "location", {
      writable: true,
      value: originalLocation,
    });
  });

  it("shows loading state while redirecting", async () => {
    const user = userEvent.setup();

    // Create a promise that we control
    let resolvePromise: (value: { url: string }) => void;
    const pendingPromise = new Promise<{ url: string }>((resolve) => {
      resolvePromise = resolve;
    });

    vi.spyOn(api.api, "get").mockReturnValue(pendingPromise);

    renderLogin();

    const button = screen.getByRole("button", { name: /sign in with github/i });
    await user.click(button);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /redirecting to github/i })
      ).toBeInTheDocument();
    });

    // Button should be disabled during loading
    expect(button).toBeDisabled();

    // Cleanup - resolve the promise
    resolvePromise!({ url: "https://github.com" });
  });

  it("displays error message when API call fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(api.api, "get").mockRejectedValue(new Error("Network error"));

    renderLogin();

    const button = screen.getByRole("button", { name: /sign in with github/i });
    await user.click(button);

    await waitFor(() => {
      expect(
        screen.getByText("Failed to initiate login. Please try again.")
      ).toBeInTheDocument();
    });

    // Button should be enabled again after error
    expect(button).not.toBeDisabled();
  });
});
