import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { OrgSelector } from "./OrgSelector";
import type { Organization } from "../types";

const mockOrganizations: Organization[] = [
  { id: "1", login: "org-one", avatar_url: "https://example.com/org1.png" },
  { id: "2", login: "org-two", avatar_url: "https://example.com/org2.png" },
  { id: "3", login: "org-three", avatar_url: "https://example.com/org3.png" },
];

describe("OrgSelector", () => {
  it("shows loading state when isLoading is true", () => {
    render(
      <OrgSelector
        organizations={[]}
        selectedOrg={null}
        onSelect={vi.fn()}
        isLoading={true}
      />
    );

    expect(screen.getByText("Loading organizations...")).toBeInTheDocument();
  });

  it("shows empty state when no organizations", () => {
    render(
      <OrgSelector
        organizations={[]}
        selectedOrg={null}
        onSelect={vi.fn()}
        isLoading={false}
      />
    );

    expect(screen.getByText("No organizations found")).toBeInTheDocument();
  });

  it("shows placeholder when no organization selected", () => {
    render(
      <OrgSelector
        organizations={mockOrganizations}
        selectedOrg={null}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText("Select organization")).toBeInTheDocument();
  });

  it("shows selected organization", () => {
    render(
      <OrgSelector
        organizations={mockOrganizations}
        selectedOrg={mockOrganizations[0]}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText("org-one")).toBeInTheDocument();
  });

  it("opens dropdown when clicked", async () => {
    const user = userEvent.setup();

    render(
      <OrgSelector
        organizations={mockOrganizations}
        selectedOrg={null}
        onSelect={vi.fn()}
      />
    );

    const button = screen.getByRole("button");
    await user.click(button);

    // All organizations should be visible in dropdown
    expect(screen.getByText("org-one")).toBeInTheDocument();
    expect(screen.getByText("org-two")).toBeInTheDocument();
    expect(screen.getByText("org-three")).toBeInTheDocument();
  });

  it("calls onSelect when organization is selected", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(
      <OrgSelector
        organizations={mockOrganizations}
        selectedOrg={null}
        onSelect={onSelect}
      />
    );

    // Open dropdown
    const button = screen.getByRole("button");
    await user.click(button);

    // Click on second organization
    const option = screen.getByText("org-two");
    await user.click(option);

    expect(onSelect).toHaveBeenCalledWith(mockOrganizations[1]);
  });

  it("closes dropdown after selection", async () => {
    const user = userEvent.setup();

    render(
      <OrgSelector
        organizations={mockOrganizations}
        selectedOrg={null}
        onSelect={vi.fn()}
      />
    );

    // Open dropdown
    const button = screen.getByRole("button");
    await user.click(button);

    // Verify dropdown is open
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    // Click on an option
    const option = screen.getByText("org-two");
    await user.click(option);

    // Dropdown should be closed
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("shows checkmark for selected organization in dropdown", async () => {
    const user = userEvent.setup();

    render(
      <OrgSelector
        organizations={mockOrganizations}
        selectedOrg={mockOrganizations[1]}
        onSelect={vi.fn()}
      />
    );

    // Open dropdown
    const button = screen.getByRole("button");
    await user.click(button);

    // Find the selected option (should have aria-selected=true)
    const options = screen.getAllByRole("option");
    const selectedOption = options.find(
      (opt) => opt.getAttribute("aria-selected") === "true"
    );

    expect(selectedOption).toHaveTextContent("org-two");
  });

  it("closes dropdown when clicking outside", async () => {
    const user = userEvent.setup();

    render(
      <div>
        <div data-testid="outside">Outside element</div>
        <OrgSelector
          organizations={mockOrganizations}
          selectedOrg={null}
          onSelect={vi.fn()}
        />
      </div>
    );

    // Open dropdown
    const button = screen.getByRole("button");
    await user.click(button);

    // Verify dropdown is open
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    // Click outside
    await user.click(screen.getByTestId("outside"));

    // Dropdown should be closed
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });
});
