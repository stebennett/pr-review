import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Navbar } from "./Navbar";
import { AuthContext, type AuthContextType } from "../contexts/AuthContext";
import type { Organization } from "../types";

const mockOrganizations: Organization[] = [
  { id: "1", login: "org-one", avatar_url: "https://example.com/org1.png" },
  { id: "2", login: "org-two", avatar_url: "https://example.com/org2.png" },
];

const mockUser = {
  id: "123",
  username: "testuser",
  email: "test@example.com",
  avatar_url: "https://example.com/avatar.png",
};

function renderWithAuth(
  authValue: Partial<AuthContextType>,
  props: Partial<React.ComponentProps<typeof Navbar>> = {}
) {
  const defaultAuthValue: AuthContextType = {
    user: mockUser,
    isLoading: false,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
    ...authValue,
  };

  const defaultProps = {
    organizations: mockOrganizations,
    selectedOrg: mockOrganizations[0],
    onOrgSelect: vi.fn(),
    isLoadingOrgs: false,
    ...props,
  };

  return render(
    <AuthContext.Provider value={defaultAuthValue}>
      <Navbar {...defaultProps} />
    </AuthContext.Provider>
  );
}

describe("Navbar", () => {
  it("renders the PR Review title", () => {
    renderWithAuth({});

    expect(screen.getByText("PR Review")).toBeInTheDocument();
  });

  it("renders the OrgSelector with selected organization", () => {
    renderWithAuth({});

    expect(screen.getByText("org-one")).toBeInTheDocument();
  });

  it("renders user avatar and username", () => {
    renderWithAuth({});

    const avatar = screen.getByAltText("testuser");
    expect(avatar).toBeInTheDocument();
    expect(avatar).toHaveAttribute("src", "https://example.com/avatar.png");
    expect(screen.getByText("testuser")).toBeInTheDocument();
  });

  it("renders sign out button", () => {
    renderWithAuth({});

    expect(screen.getByText("Sign out")).toBeInTheDocument();
  });

  it("calls logout when sign out is clicked", async () => {
    const user = userEvent.setup();
    const logout = vi.fn();

    renderWithAuth({ logout });

    const signOutButton = screen.getByText("Sign out");
    await user.click(signOutButton);

    expect(logout).toHaveBeenCalled();
  });

  it("calls onOrgSelect when organization is selected", async () => {
    const user = userEvent.setup();
    const onOrgSelect = vi.fn();

    renderWithAuth({}, { onOrgSelect, selectedOrg: null });

    // Open dropdown
    const dropdownButton = screen.getByRole("button", {
      name: /select organization/i,
    });
    await user.click(dropdownButton);

    // Select an org
    await user.click(screen.getByText("org-two"));

    expect(onOrgSelect).toHaveBeenCalledWith(mockOrganizations[1]);
  });

  it("shows loading state for organizations", () => {
    renderWithAuth({}, { isLoadingOrgs: true });

    expect(screen.getByText("Loading organizations...")).toBeInTheDocument();
  });

  it("renders without user avatar when not available", () => {
    renderWithAuth({ user: { ...mockUser, avatar_url: null } });

    expect(screen.queryByAltText("testuser")).not.toBeInTheDocument();
    expect(screen.getByText("testuser")).toBeInTheDocument();
  });

  it("renders refresh button", () => {
    renderWithAuth({});

    const refreshButton = screen.getByTitle("Refresh");
    expect(refreshButton).toBeInTheDocument();
  });
});
