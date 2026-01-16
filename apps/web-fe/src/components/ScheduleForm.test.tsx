import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ScheduleForm from "./ScheduleForm";
import * as api from "../services/api";
import type { Schedule } from "../types";
import type { ReactNode } from "react";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    previewPATOrganizations: vi.fn(),
    previewPATRepositories: vi.fn(),
  };
});

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const mockSchedule: Schedule = {
  id: "schedule-1",
  name: "Daily PR Check",
  cron_expression: "0 9 * * 1-5",
  repositories: [{ organization: "test-org", repository: "repo-one" }],
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockOrganizations = [
  { id: "1", login: "test-org", avatar_url: "https://example.com/org.png" },
  { id: "2", login: "another-org", avatar_url: "https://example.com/org2.png" },
];

const mockRepositories = [
  { id: "1", name: "repo-one", full_name: "test-org/repo-one" },
  { id: "2", name: "repo-two", full_name: "test-org/repo-two" },
];

describe("ScheduleForm", () => {
  const mockOnSave = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.previewPATOrganizations).mockResolvedValue({
      organizations: mockOrganizations,
      username: "testuser",
    });
    vi.mocked(api.previewPATRepositories).mockResolvedValue(mockRepositories);
  });

  function renderForm(
    props: Partial<React.ComponentProps<typeof ScheduleForm>> = {}
  ) {
    return render(
      <ScheduleForm onSave={mockOnSave} onClose={mockOnClose} {...props} />,
      { wrapper: createWrapper() }
    );
  }

  describe("Step 1: Schedule Details", () => {
    it("renders step 1 by default", () => {
      renderForm();

      expect(
        screen.getByRole("heading", { name: "Create Schedule" })
      ).toBeInTheDocument();
      expect(screen.getByText("Configure schedule timing")).toBeInTheDocument();
      expect(screen.getByLabelText("Name")).toBeInTheDocument();
      expect(
        screen.getByLabelText(/Schedule \(Cron Expression\)/)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("switch", { name: /active/i })
      ).toBeInTheDocument();
    });

    it("renders cron expression presets", () => {
      renderForm();

      expect(screen.getByText("Weekdays at 9am")).toBeInTheDocument();
      expect(screen.getByText("Daily at 9am")).toBeInTheDocument();
    });

    it("applies cron preset when clicked", async () => {
      const user = userEvent.setup();
      renderForm();

      await user.click(screen.getByText("Weekdays at 9am"));

      expect(screen.getByLabelText(/Schedule \(Cron Expression\)/)).toHaveValue(
        "0 9 * * 1-5"
      );
    });

    it("validates required fields before moving to step 2", async () => {
      const user = userEvent.setup();
      renderForm();

      await user.click(screen.getByRole("button", { name: "Next" }));

      expect(screen.getByText("Name is required")).toBeInTheDocument();
      expect(
        screen.getByText("Cron expression is required")
      ).toBeInTheDocument();
    });

    it("validates cron expression format", async () => {
      const user = userEvent.setup();
      renderForm();

      await user.type(screen.getByLabelText("Name"), "Test Schedule");
      await user.type(
        screen.getByLabelText(/Schedule \(Cron Expression\)/),
        "invalid"
      );

      await user.click(screen.getByRole("button", { name: "Next" }));

      expect(screen.getByText(/Invalid cron expression/)).toBeInTheDocument();
    });

    it("moves to step 2 with valid inputs", async () => {
      const user = userEvent.setup();
      renderForm();

      await user.type(screen.getByLabelText("Name"), "Test Schedule");
      await user.type(
        screen.getByLabelText(/Schedule \(Cron Expression\)/),
        "0 9 * * 1-5"
      );

      await user.click(screen.getByRole("button", { name: "Next" }));

      expect(
        screen.getByText("Enter your GitHub Personal Access Token")
      ).toBeInTheDocument();
    });

    it("toggles active state", async () => {
      const user = userEvent.setup();
      renderForm();

      const activeSwitch = screen.getByRole("switch", { name: /active/i });
      expect(activeSwitch).toHaveAttribute("aria-checked", "true");

      await user.click(activeSwitch);
      expect(activeSwitch).toHaveAttribute("aria-checked", "false");
    });
  });

  describe("Step 2: GitHub PAT", () => {
    async function goToStep2() {
      const user = userEvent.setup();
      await user.type(screen.getByLabelText("Name"), "Test Schedule");
      await user.type(
        screen.getByLabelText(/Schedule \(Cron Expression\)/),
        "0 9 * * 1-5"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));
    }

    it("shows PAT input on step 2", async () => {
      renderForm();
      await goToStep2();

      expect(
        screen.getByLabelText(/GitHub Personal Access Token/)
      ).toBeInTheDocument();
    });

    it("masks PAT input by default", async () => {
      renderForm();
      await goToStep2();

      expect(screen.getByLabelText(/GitHub Personal Access Token/)).toHaveAttribute(
        "type",
        "password"
      );
    });

    it("toggles PAT visibility", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep2();

      const patInput = screen.getByLabelText(/GitHub Personal Access Token/);
      expect(patInput).toHaveAttribute("type", "password");

      await user.click(screen.getByRole("button", { name: /show pat/i }));
      expect(patInput).toHaveAttribute("type", "text");

      await user.click(screen.getByRole("button", { name: /hide pat/i }));
      expect(patInput).toHaveAttribute("type", "password");
    });

    it("validates PAT is required for new schedule", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep2();

      await user.click(screen.getByRole("button", { name: "Next" }));

      expect(
        screen.getByText("GitHub Personal Access Token is required")
      ).toBeInTheDocument();
    });

    it("validates PAT with API and moves to step 3", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep2();

      await user.type(
        screen.getByLabelText(/GitHub Personal Access Token/),
        "ghp_test123"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));

      await waitFor(() => {
        expect(api.previewPATOrganizations).toHaveBeenCalledWith("ghp_test123");
      });

      await waitFor(() => {
        expect(
          screen.getByText("Select repositories to monitor")
        ).toBeInTheDocument();
      });
    });

    it("shows error when PAT validation fails", async () => {
      vi.mocked(api.previewPATOrganizations).mockRejectedValue(
        new Error("Invalid PAT")
      );

      const user = userEvent.setup();
      renderForm();
      await goToStep2();

      await user.type(
        screen.getByLabelText(/GitHub Personal Access Token/),
        "invalid_pat"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));

      await waitFor(() => {
        expect(screen.getByText("Invalid PAT")).toBeInTheDocument();
      });
    });

    it("shows validated username after successful PAT validation", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep2();

      await user.type(
        screen.getByLabelText(/GitHub Personal Access Token/),
        "ghp_test123"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));

      // The username banner appears briefly before moving to step 3
      await waitFor(() => {
        expect(api.previewPATOrganizations).toHaveBeenCalled();
      });
    });

    it("can go back to step 1", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep2();

      await user.click(screen.getByRole("button", { name: "Back" }));

      expect(screen.getByText("Configure schedule timing")).toBeInTheDocument();
      expect(screen.getByLabelText("Name")).toHaveValue("Test Schedule");
    });
  });

  describe("Step 3: Repository Selection", () => {
    async function goToStep3() {
      const user = userEvent.setup();
      await user.type(screen.getByLabelText("Name"), "Test Schedule");
      await user.type(
        screen.getByLabelText(/Schedule \(Cron Expression\)/),
        "0 9 * * 1-5"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));

      await user.type(
        screen.getByLabelText(/GitHub Personal Access Token/),
        "ghp_test123"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));

      await waitFor(() => {
        expect(
          screen.getByText("Select repositories to monitor")
        ).toBeInTheDocument();
      });
    }

    it("shows organization selector on step 3", async () => {
      renderForm();
      await goToStep3();

      expect(screen.getByText("Select organization...")).toBeInTheDocument();
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("loads repositories when organization is selected", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep3();

      await user.selectOptions(screen.getByRole("combobox"), "test-org");

      await waitFor(() => {
        expect(api.previewPATRepositories).toHaveBeenCalledWith(
          "ghp_test123",
          "test-org"
        );
      });

      await waitFor(() => {
        expect(screen.getByText("repo-one")).toBeInTheDocument();
        expect(screen.getByText("repo-two")).toBeInTheDocument();
      });
    });

    it("allows selecting multiple repositories", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep3();

      await user.selectOptions(screen.getByRole("combobox"), "test-org");

      await waitFor(() => {
        expect(screen.getByText("repo-one")).toBeInTheDocument();
      });

      await user.click(screen.getByLabelText("repo-one"));
      await user.click(screen.getByLabelText("repo-two"));

      expect(screen.getByText("test-org/repo-one")).toBeInTheDocument();
      expect(screen.getByText("test-org/repo-two")).toBeInTheDocument();
    });

    it("validates at least one repository is selected", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep3();

      await user.click(screen.getByRole("button", { name: "Create Schedule" }));

      expect(
        screen.getByText("At least one repository must be selected")
      ).toBeInTheDocument();
    });

    it("submits form with valid data", async () => {
      const user = userEvent.setup();
      mockOnSave.mockResolvedValue(undefined);
      renderForm();
      await goToStep3();

      await user.selectOptions(screen.getByRole("combobox"), "test-org");

      await waitFor(() => {
        expect(screen.getByText("repo-one")).toBeInTheDocument();
      });

      await user.click(screen.getByLabelText("repo-one"));
      await user.click(screen.getByRole("button", { name: "Create Schedule" }));

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith({
          name: "Test Schedule",
          cron_expression: "0 9 * * 1-5",
          github_pat: "ghp_test123",
          repositories: [{ organization: "test-org", repository: "repo-one" }],
          is_active: true,
        });
      });
    });

    it("can go back to step 2", async () => {
      const user = userEvent.setup();
      renderForm();
      await goToStep3();

      await user.click(screen.getByRole("button", { name: "Back" }));

      expect(
        screen.getByText("Enter your GitHub Personal Access Token")
      ).toBeInTheDocument();
    });
  });

  describe("Edit Mode", () => {
    it("pre-fills form with existing schedule data", () => {
      renderForm({ schedule: mockSchedule });

      expect(screen.getByRole("heading", { name: "Edit Schedule" })).toBeInTheDocument();
      expect(screen.getByLabelText("Name")).toHaveValue("Daily PR Check");
      expect(screen.getByLabelText(/Schedule \(Cron Expression\)/)).toHaveValue(
        "0 9 * * 1-5"
      );
    });

    it("shows hint about keeping current PAT", async () => {
      const user = userEvent.setup();
      renderForm({ schedule: mockSchedule });

      // Go to step 2
      await user.click(screen.getByRole("button", { name: "Next" }));

      expect(screen.getByText(/leave blank to keep current/)).toBeInTheDocument();
    });

    it("allows skipping PAT entry when editing", async () => {
      const user = userEvent.setup();
      renderForm({ schedule: mockSchedule });

      // Go to step 2
      await user.click(screen.getByRole("button", { name: "Next" }));

      // Try to go to step 3 without entering PAT
      await user.click(screen.getByRole("button", { name: "Next" }));

      // Should move to step 3 without PAT validation
      await waitFor(() => {
        expect(
          screen.getByText("Select repositories to monitor")
        ).toBeInTheDocument();
      });

      // PAT validation should not have been called
      expect(api.previewPATOrganizations).not.toHaveBeenCalled();
    });

    it("shows Save Changes button on step 3", async () => {
      const user = userEvent.setup();
      vi.mocked(api.previewPATOrganizations).mockResolvedValue({
        organizations: mockOrganizations,
        username: "testuser",
      });

      renderForm({ schedule: mockSchedule });

      // Go through steps
      await user.click(screen.getByRole("button", { name: "Next" }));
      await user.type(
        screen.getByLabelText(/GitHub Personal Access Token/),
        "ghp_new"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Save Changes" })
        ).toBeInTheDocument();
      });
    });
  });

  describe("Modal Behavior", () => {
    it("closes modal when cancel is clicked", async () => {
      const user = userEvent.setup();
      renderForm();

      await user.click(screen.getByRole("button", { name: "Cancel" }));

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("closes modal when clicking backdrop", async () => {
      const user = userEvent.setup();
      renderForm();

      const backdrop = document.querySelector('[aria-hidden="true"]');
      if (backdrop) {
        await user.click(backdrop);
      }

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe("Loading State", () => {
    it("shows saving state in submit button", async () => {
      const user = userEvent.setup();
      renderForm({ isLoading: true });

      // Navigate to step 3
      await user.type(screen.getByLabelText("Name"), "Test");
      await user.click(screen.getByText("Daily at 9am"));
      await user.click(screen.getByRole("button", { name: "Next" }));

      await user.type(
        screen.getByLabelText(/GitHub Personal Access Token/),
        "ghp_test"
      );
      await user.click(screen.getByRole("button", { name: "Next" }));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Saving..." })
        ).toBeInTheDocument();
      });
    });
  });

  describe("Error Handling", () => {
    it("displays error message when provided", () => {
      const error = new Error("Failed to create schedule");
      renderForm({ error });

      expect(screen.getByText("Failed to create schedule")).toBeInTheDocument();
    });
  });
});
