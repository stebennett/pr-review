import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { RepoList } from "./RepoList";
import * as api from "../services/api";
import type { ReactNode } from "react";

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

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const mockRepositories = [
  { id: "1", name: "repo-1", full_name: "my-org/repo-1" },
  { id: "2", name: "repo-2", full_name: "my-org/repo-2" },
];

const mockPullRequests = [
  {
    number: 1,
    title: "Add authentication feature",
    author: { username: "octocat", avatar_url: "https://example.com/octocat.png" },
    labels: [{ name: "enhancement", color: "84b6eb" }],
    checks_status: "pass",
    html_url: "https://github.com/my-org/repo-1/pull/1",
    created_at: "2024-01-10T08:00:00Z",
  },
  {
    number: 2,
    title: "Fix bug in login",
    author: { username: "dev1", avatar_url: "https://example.com/dev1.png" },
    labels: [{ name: "bug", color: "d73a4a" }],
    checks_status: "fail",
    html_url: "https://github.com/my-org/repo-1/pull/2",
    created_at: "2024-01-12T10:00:00Z",
  },
];

describe("RepoList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state while fetching repositories", () => {
    (api.api.get as Mock).mockImplementation(() => new Promise(() => {}));

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    // Should show skeleton loading state
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("displays repositories when loaded", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { repositories: mockRepositories },
    });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    expect(screen.getByText("my-org/repo-2")).toBeInTheDocument();
  });

  it("shows error message when fetch fails", async () => {
    (api.api.get as Mock).mockRejectedValue(new Error("Network error"));

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Failed to load repositories")).toBeInTheDocument();
    });
  });

  it("shows empty state when no repositories", async () => {
    (api.api.get as Mock).mockResolvedValue({
      data: { repositories: [] },
    });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("No repositories found")).toBeInTheDocument();
    });
  });

  it("expands repository to show pull requests when clicked", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock)
      .mockResolvedValueOnce({ data: { repositories: mockRepositories } })
      .mockResolvedValueOnce({ data: { pulls: mockPullRequests } });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    // Click to expand first repo
    await user.click(screen.getByText("my-org/repo-1"));

    // Should show pull requests
    await waitFor(() => {
      expect(screen.getByText("Add authentication feature")).toBeInTheDocument();
    });

    expect(screen.getByText("Fix bug in login")).toBeInTheDocument();
  });

  it("collapses repository when clicked again", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock)
      .mockResolvedValueOnce({ data: { repositories: mockRepositories } })
      .mockResolvedValueOnce({ data: { pulls: mockPullRequests } });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    // Click to expand
    await user.click(screen.getByText("my-org/repo-1"));

    await waitFor(() => {
      expect(screen.getByText("Add authentication feature")).toBeInTheDocument();
    });

    // Click to collapse
    await user.click(screen.getByText("my-org/repo-1"));

    // PRs should no longer be visible
    expect(screen.queryByText("Add authentication feature")).not.toBeInTheDocument();
  });

  it("shows PR count badge for repository", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock)
      .mockResolvedValueOnce({ data: { repositories: mockRepositories } })
      .mockResolvedValueOnce({ data: { pulls: mockPullRequests } });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    // Click to expand and load PRs
    await user.click(screen.getByText("my-org/repo-1"));

    // Wait for PR count to update
    await waitFor(() => {
      expect(screen.getByText("2")).toBeInTheDocument();
    });
  });

  it("shows empty PRs message when repository has no open PRs", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock)
      .mockResolvedValueOnce({ data: { repositories: mockRepositories } })
      .mockResolvedValueOnce({ data: { pulls: [] } });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    await user.click(screen.getByText("my-org/repo-1"));

    await waitFor(() => {
      expect(screen.getByText("No open pull requests")).toBeInTheDocument();
    });
  });

  it("displays check status icons correctly", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock)
      .mockResolvedValueOnce({ data: { repositories: mockRepositories } })
      .mockResolvedValueOnce({ data: { pulls: mockPullRequests } });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    await user.click(screen.getByText("my-org/repo-1"));

    await waitFor(() => {
      expect(screen.getByText("Add authentication feature")).toBeInTheDocument();
    });

    // Check for pass icon (green checkmark)
    expect(screen.getByTitle("Checks passed")).toBeInTheDocument();
    // Check for fail icon (red x)
    expect(screen.getByTitle("Checks failed")).toBeInTheDocument();
  });

  it("renders PR labels with correct colors", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock)
      .mockResolvedValueOnce({ data: { repositories: mockRepositories } })
      .mockResolvedValueOnce({ data: { pulls: mockPullRequests } });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    await user.click(screen.getByText("my-org/repo-1"));

    await waitFor(() => {
      expect(screen.getByText("enhancement")).toBeInTheDocument();
    });

    expect(screen.getByText("bug")).toBeInTheDocument();
  });

  it("PR title links to GitHub", async () => {
    const user = userEvent.setup();

    (api.api.get as Mock)
      .mockResolvedValueOnce({ data: { repositories: mockRepositories } })
      .mockResolvedValueOnce({ data: { pulls: mockPullRequests } });

    render(<RepoList org="my-org" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("my-org/repo-1")).toBeInTheDocument();
    });

    await user.click(screen.getByText("my-org/repo-1"));

    await waitFor(() => {
      const prLink = screen.getByRole("link", { name: /Add authentication feature/ });
      expect(prLink).toHaveAttribute(
        "href",
        "https://github.com/my-org/repo-1/pull/1"
      );
      expect(prLink).toHaveAttribute("target", "_blank");
    });
  });
});
