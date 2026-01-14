import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PullRequestCard, CheckStatusIcon } from "./PullRequestCard";
import type { PullRequest } from "../types";

// Mock date-fns to return predictable values
vi.mock("../utils/date", () => ({
  formatRelativeTime: vi.fn(() => "3 days ago"),
}));

const createMockPR = (overrides: Partial<PullRequest> = {}): PullRequest => ({
  number: 123,
  title: "Add authentication feature",
  author: {
    username: "octocat",
    avatar_url: "https://example.com/octocat.png",
  },
  labels: [
    { name: "enhancement", color: "84b6eb" },
    { name: "high-priority", color: "d73a4a" },
  ],
  checks_status: "pass",
  html_url: "https://github.com/my-org/my-repo/pull/123",
  created_at: "2024-01-10T08:00:00Z",
  ...overrides,
});

describe("CheckStatusIcon", () => {
  it('renders green checkmark for "pass" status', () => {
    render(<CheckStatusIcon status="pass" />);

    const icon = screen.getByTitle("Checks passed");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass("text-green-600");
    expect(icon).toHaveTextContent("✓");
  });

  it('renders red X for "fail" status', () => {
    render(<CheckStatusIcon status="fail" />);

    const icon = screen.getByTitle("Checks failed");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass("text-red-600");
    expect(icon).toHaveTextContent("✗");
  });

  it('renders yellow circle for "pending" status', () => {
    render(<CheckStatusIcon status="pending" />);

    const icon = screen.getByTitle("Checks pending");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass("text-yellow-600");
    expect(icon).toHaveTextContent("●");
  });

  it('renders gray circle for "unknown" status', () => {
    render(<CheckStatusIcon status="unknown" />);

    const icon = screen.getByTitle("No checks");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass("text-gray-400");
    expect(icon).toHaveTextContent("○");
  });
});

describe("PullRequestCard", () => {
  it("renders PR title as a link", () => {
    const pr = createMockPR();
    render(<PullRequestCard pr={pr} />);

    const link = screen.getByRole("link", { name: /Add authentication feature/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "https://github.com/my-org/my-repo/pull/123");
  });

  it("opens link in new tab with security attributes", () => {
    const pr = createMockPR();
    render(<PullRequestCard pr={pr} />);

    const link = screen.getByRole("link", { name: /Add authentication feature/i });
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("displays relative time", () => {
    const pr = createMockPR();
    render(<PullRequestCard pr={pr} />);

    expect(screen.getByText("3 days ago")).toBeInTheDocument();
  });

  it("renders labels with correct colors", () => {
    const pr = createMockPR();
    render(<PullRequestCard pr={pr} />);

    const enhancementLabel = screen.getByText("enhancement");
    expect(enhancementLabel).toBeInTheDocument();
    expect(enhancementLabel).toHaveStyle({
      backgroundColor: "#84b6eb20",
      color: "#84b6eb",
      border: "1px solid #84b6eb40",
    });

    const priorityLabel = screen.getByText("high-priority");
    expect(priorityLabel).toBeInTheDocument();
    expect(priorityLabel).toHaveStyle({
      backgroundColor: "#d73a4a20",
      color: "#d73a4a",
      border: "1px solid #d73a4a40",
    });
  });

  it("renders author avatar and username", () => {
    const pr = createMockPR();
    render(<PullRequestCard pr={pr} />);

    const avatar = screen.getByAltText("octocat");
    expect(avatar).toBeInTheDocument();
    expect(avatar).toHaveAttribute("src", "https://example.com/octocat.png");
    expect(avatar).toHaveClass("w-4", "h-4", "rounded-full");

    expect(screen.getByText("octocat")).toBeInTheDocument();
  });

  it("renders checks status icon", () => {
    const pr = createMockPR({ checks_status: "pass" });
    render(<PullRequestCard pr={pr} />);

    expect(screen.getByTitle("Checks passed")).toBeInTheDocument();
  });

  it("handles PR with no labels", () => {
    const pr = createMockPR({ labels: [] });
    render(<PullRequestCard pr={pr} />);

    // Should still render the card without labels section
    expect(screen.getByText("Add authentication feature")).toBeInTheDocument();
    expect(screen.queryByText("enhancement")).not.toBeInTheDocument();
  });

  it("renders different checks statuses correctly", () => {
    const { rerender } = render(
      <PullRequestCard pr={createMockPR({ checks_status: "fail" })} />
    );
    expect(screen.getByTitle("Checks failed")).toBeInTheDocument();

    rerender(<PullRequestCard pr={createMockPR({ checks_status: "pending" })} />);
    expect(screen.getByTitle("Checks pending")).toBeInTheDocument();

    rerender(<PullRequestCard pr={createMockPR({ checks_status: "unknown" })} />);
    expect(screen.getByTitle("No checks")).toBeInTheDocument();
  });

  it("displays long titles with truncation", () => {
    const longTitle = "This is a very long pull request title that should be truncated when it exceeds the available space";
    const pr = createMockPR({ title: longTitle });
    render(<PullRequestCard pr={pr} />);

    const link = screen.getByRole("link", { name: longTitle });
    expect(link).toHaveClass("truncate");
  });
});
