import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import Settings from "./Settings";
import { AuthProvider } from "../contexts/AuthContext";
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
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
    hasAuthToken: vi.fn(),
  };
});

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

function renderSettings() {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/settings"]}>
        <AuthProvider>
          <Settings />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Settings", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();

    // Mock authenticated user
    localStorage.setItem("token", "test-token");
    vi.mocked(api.hasAuthToken).mockReturnValue(true);
    vi.mocked(api.api.get).mockResolvedValue({
      data: {
        id: "123",
        username: "testuser",
        email: "test@example.com",
        avatar_url: "https://example.com/avatar.png",
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the settings page with title", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: "test@example.com" });

    renderSettings();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Settings", level: 1 })).toBeInTheDocument();
    });
  });

  it("renders the email address section", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: "test@example.com" });

    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Email Address")).toBeInTheDocument();
    });
    expect(
      screen.getByText("This email will be used for notification schedules.")
    ).toBeInTheDocument();
  });

  it("displays loading state while fetching settings", async () => {
    let resolveSettings: (value: { email: string | null }) => void;
    const pendingPromise = new Promise<{ email: string | null }>((resolve) => {
      resolveSettings = resolve;
    });
    vi.mocked(api.getSettings).mockReturnValue(pendingPromise);

    renderSettings();

    expect(screen.getByText("Loading settings...")).toBeInTheDocument();

    resolveSettings!({ email: "test@example.com" });

    await waitFor(() => {
      expect(screen.queryByText("Loading settings...")).not.toBeInTheDocument();
    });
  });

  it("displays current email from API", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: "user@domain.com" });

    renderSettings();

    await waitFor(() => {
      const input = screen.getByPlaceholderText("Enter your email address");
      expect(input).toHaveValue("user@domain.com");
    });
  });

  it("allows email input to be changed", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getSettings).mockResolvedValue({ email: "" });

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter your email address")
      ).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Enter your email address");
    await user.clear(input);
    await user.type(input, "new@example.com");

    expect(input).toHaveValue("new@example.com");
  });

  it("shows validation error for empty email", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getSettings).mockResolvedValue({ email: "" });

    renderSettings();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    });

    const saveButton = screen.getByRole("button", { name: "Save" });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText("Email address is required")).toBeInTheDocument();
    });
  });

  it("shows validation error for invalid email format", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getSettings).mockResolvedValue({ email: "" });

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter your email address")
      ).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Enter your email address");
    await user.type(input, "invalid-email");

    const saveButton = screen.getByRole("button", { name: "Save" });
    await user.click(saveButton);

    await waitFor(() => {
      expect(
        screen.getByText("Please enter a valid email address")
      ).toBeInTheDocument();
    });
  });

  it("calls updateSettings when save button is clicked with valid email", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getSettings).mockResolvedValue({ email: "" });
    vi.mocked(api.updateSettings).mockResolvedValue({
      email: "new@example.com",
    });

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter your email address")
      ).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Enter your email address");
    await user.type(input, "new@example.com");

    const saveButton = screen.getByRole("button", { name: "Save" });
    await user.click(saveButton);

    await waitFor(() => {
      expect(api.updateSettings).toHaveBeenCalledWith({
        email: "new@example.com",
      });
    });
  });

  it("shows success message after saving email", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getSettings).mockResolvedValue({ email: "" });
    vi.mocked(api.updateSettings).mockResolvedValue({
      email: "new@example.com",
    });

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter your email address")
      ).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Enter your email address");
    await user.type(input, "new@example.com");

    const saveButton = screen.getByRole("button", { name: "Save" });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText("Email updated successfully.")).toBeInTheDocument();
    });
  });

  it("shows error message when update fails", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getSettings).mockResolvedValue({ email: "" });
    vi.mocked(api.updateSettings).mockRejectedValue(new Error("Update failed"));

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter your email address")
      ).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Enter your email address");
    await user.type(input, "new@example.com");

    const saveButton = screen.getByRole("button", { name: "Save" });
    await user.click(saveButton);

    await waitFor(() => {
      expect(
        screen.getByText("Failed to update email. Please try again.")
      ).toBeInTheDocument();
    });
  });

  it("shows loading state on save button while updating", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getSettings).mockResolvedValue({ email: "" });

    let resolveUpdate: (value: { email: string }) => void;
    const pendingPromise = new Promise<{ email: string }>((resolve) => {
      resolveUpdate = resolve;
    });
    vi.mocked(api.updateSettings).mockReturnValue(pendingPromise);

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Enter your email address")
      ).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Enter your email address");
    await user.type(input, "new@example.com");

    const saveButton = screen.getByRole("button", { name: "Save" });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Saving..." })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();

    resolveUpdate!({ email: "new@example.com" });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    });
  });

  it("renders the notification schedules section", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: "test@example.com" });

    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("Notification Schedules")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: "+ Add Schedule" })
    ).toBeInTheDocument();
  });

  it("shows empty state for notification schedules", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: "test@example.com" });

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByText("No notification schedules configured yet.")
      ).toBeInTheDocument();
    });
  });

  it("displays error when settings fail to load", async () => {
    vi.mocked(api.getSettings).mockRejectedValue(new Error("Network error"));

    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByText("Failed to load settings. Please try again.")
      ).toBeInTheDocument();
    });
  });

  it("has a link back to the dashboard", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: "test@example.com" });

    renderSettings();

    await waitFor(() => {
      const prReviewLink = screen.getByRole("link", { name: "PR Review" });
      expect(prReviewLink).toBeInTheDocument();
      expect(prReviewLink).toHaveAttribute("href", "/");
    });
  });

  it("displays sign out button in the navbar", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: "test@example.com" });

    renderSettings();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
    });
  });

  it("handles null email from settings", async () => {
    vi.mocked(api.getSettings).mockResolvedValue({ email: null });

    renderSettings();

    await waitFor(() => {
      const input = screen.getByPlaceholderText("Enter your email address");
      expect(input).toHaveValue("");
    });
  });
});
