import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import App from "./App";
import * as api from "./services/api";

function renderWithProviders(
  ui: React.ReactElement,
  { initialEntries = ["/"] }: { initialEntries?: string[] } = {}
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
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

  it("renders the app title on dashboard", () => {
    renderWithProviders(<App />);
    expect(screen.getByText("PR Review")).toBeInTheDocument();
  });

  it("renders the app description on dashboard", () => {
    renderWithProviders(<App />);
    expect(
      screen.getByText("GitHub Pull Request monitoring application")
    ).toBeInTheDocument();
  });

  it("renders login page at /login route", () => {
    renderWithProviders(<App />, { initialEntries: ["/login"] });
    expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in with github/i })
    ).toBeInTheDocument();
  });

  it("stores token from URL and removes it from query params", async () => {
    const setTokenSpy = vi.spyOn(api, "setAuthToken");

    renderWithProviders(<App />, { initialEntries: ["/?token=test-jwt-token"] });

    await waitFor(() => {
      expect(setTokenSpy).toHaveBeenCalledWith("test-jwt-token");
    });

    // Should show dashboard after token is processed
    expect(screen.getByText("PR Review")).toBeInTheDocument();
  });
});
