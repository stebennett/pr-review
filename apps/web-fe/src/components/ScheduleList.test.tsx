import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ScheduleList from "./ScheduleList";
import type { Schedule } from "../types";

const mockSchedules: Schedule[] = [
  {
    id: "schedule-1",
    name: "Daily PR Check",
    cron_expression: "0 9 * * *",
    repositories: [
      { organization: "test-org", repository: "repo-one" },
      { organization: "test-org", repository: "repo-two" },
    ],
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "schedule-2",
    name: "Weekday Updates",
    cron_expression: "0 9 * * 1-5",
    repositories: [{ organization: "another-org", repository: "project" }],
    is_active: false,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("ScheduleList", () => {
  const mockOnEdit = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnToggleActive = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnDelete.mockResolvedValue(undefined);
    mockOnToggleActive.mockResolvedValue(undefined);
  });

  function renderScheduleList(
    props: Partial<React.ComponentProps<typeof ScheduleList>> = {}
  ) {
    return render(
      <ScheduleList
        schedules={mockSchedules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggleActive={mockOnToggleActive}
        {...props}
      />
    );
  }

  describe("rendering", () => {
    it("renders all schedules", () => {
      renderScheduleList();

      expect(screen.getByText("Daily PR Check")).toBeInTheDocument();
      expect(screen.getByText("Weekday Updates")).toBeInTheDocument();
    });

    it("displays schedule name", () => {
      renderScheduleList();

      expect(screen.getByText("Daily PR Check")).toBeInTheDocument();
    });

    it("displays human-readable cron expression", () => {
      renderScheduleList();

      expect(screen.getByText("Daily at 9:00 AM")).toBeInTheDocument();
      expect(screen.getByText("Weekdays at 9:00 AM")).toBeInTheDocument();
    });

    it("displays repository count (singular)", () => {
      renderScheduleList();

      expect(screen.getByText("1 repository")).toBeInTheDocument();
    });

    it("displays repository count (plural)", () => {
      renderScheduleList();

      expect(screen.getByText("2 repositories")).toBeInTheDocument();
    });

    it("displays active badge for active schedules", () => {
      renderScheduleList();

      const activeBadges = screen.getAllByText("Active");
      expect(activeBadges.length).toBeGreaterThan(0);
    });

    it("displays inactive badge for inactive schedules", () => {
      renderScheduleList();

      expect(screen.getByText("Inactive")).toBeInTheDocument();
    });

    it("renders edit button for each schedule", () => {
      renderScheduleList();

      const editButtons = screen.getAllByText("Edit");
      expect(editButtons).toHaveLength(2);
    });

    it("renders delete button for each schedule", () => {
      renderScheduleList();

      const deleteButtons = screen.getAllByRole("button", {
        name: /delete/i,
      });
      expect(deleteButtons).toHaveLength(2);
    });
  });

  describe("edit functionality", () => {
    it("calls onEdit with correct schedule when edit button clicked", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const editButtons = screen.getAllByText("Edit");
      await user.click(editButtons[0]);

      expect(mockOnEdit).toHaveBeenCalledTimes(1);
      expect(mockOnEdit).toHaveBeenCalledWith(mockSchedules[0]);
    });
  });

  describe("toggle functionality", () => {
    it("calls onToggleActive when status badge clicked", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const activeButton = screen.getByRole("button", {
        name: /toggle daily pr check/i,
      });
      await user.click(activeButton);

      expect(mockOnToggleActive).toHaveBeenCalledTimes(1);
      expect(mockOnToggleActive).toHaveBeenCalledWith(mockSchedules[0], false);
    });

    it("passes correct value when toggling inactive to active", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const inactiveButton = screen.getByRole("button", {
        name: /toggle weekday updates/i,
      });
      await user.click(inactiveButton);

      expect(mockOnToggleActive).toHaveBeenCalledWith(mockSchedules[1], true);
    });

    it("disables toggle button when isToggling is true", () => {
      renderScheduleList({ isToggling: true });

      const toggleButtons = screen.getAllByRole("button", {
        name: /toggle/i,
      });
      toggleButtons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe("delete functionality", () => {
    it("shows confirmation dialog when delete button clicked", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const deleteButton = screen.getByRole("button", {
        name: /delete daily pr check/i,
      });
      await user.click(deleteButton);

      expect(screen.getByText("Delete Schedule")).toBeInTheDocument();
      expect(
        screen.getByText(/are you sure you want to delete "Daily PR Check"/i)
      ).toBeInTheDocument();
    });

    it("closes confirmation dialog when cancel clicked", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const deleteButton = screen.getByRole("button", {
        name: /delete daily pr check/i,
      });
      await user.click(deleteButton);

      const cancelButton = screen.getByRole("button", { name: "Cancel" });
      await user.click(cancelButton);

      expect(screen.queryByText("Delete Schedule")).not.toBeInTheDocument();
      expect(mockOnDelete).not.toHaveBeenCalled();
    });

    it("calls onDelete when confirm delete clicked", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const deleteButton = screen.getByRole("button", {
        name: /delete daily pr check/i,
      });
      await user.click(deleteButton);

      const confirmButton = screen.getByRole("button", { name: "Delete" });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockOnDelete).toHaveBeenCalledTimes(1);
        expect(mockOnDelete).toHaveBeenCalledWith(mockSchedules[0]);
      });
    });

    it("closes dialog after successful deletion", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const deleteButton = screen.getByRole("button", {
        name: /delete daily pr check/i,
      });
      await user.click(deleteButton);

      const confirmButton = screen.getByRole("button", { name: "Delete" });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(screen.queryByText("Delete Schedule")).not.toBeInTheDocument();
      });
    });

    it("shows loading state in dialog when isDeleting is true", async () => {
      const user = userEvent.setup();
      // First render with isDeleting false so we can open the dialog
      const { rerender } = render(
        <ScheduleList
          schedules={mockSchedules}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onToggleActive={mockOnToggleActive}
          isDeleting={false}
        />
      );

      // Open the confirmation dialog
      const deleteButton = screen.getByRole("button", {
        name: /delete daily pr check/i,
      });
      await user.click(deleteButton);

      // Rerender with isDeleting true to simulate deletion in progress
      rerender(
        <ScheduleList
          schedules={mockSchedules}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onToggleActive={mockOnToggleActive}
          isDeleting={true}
        />
      );

      // The dialog should show "Deleting..." when isDeleting is true
      expect(screen.getByText("Deleting...")).toBeInTheDocument();
    });

    it("disables delete button when isDeleting is true", () => {
      renderScheduleList({ isDeleting: true });

      const deleteButtons = screen.getAllByRole("button", {
        name: /delete/i,
      });
      deleteButtons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });

    it("closes dialog when clicking backdrop", async () => {
      const user = userEvent.setup();
      renderScheduleList();

      const deleteButton = screen.getByRole("button", {
        name: /delete daily pr check/i,
      });
      await user.click(deleteButton);

      // Click the backdrop (the overlay div)
      const backdrop = document.querySelector(".bg-gray-500");
      if (backdrop) {
        await user.click(backdrop);
      }

      expect(screen.queryByText("Delete Schedule")).not.toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("renders nothing when schedules array is empty", () => {
      const { container } = renderScheduleList({ schedules: [] });

      // The component renders an empty div with space-y-3 class
      expect(container.querySelector(".space-y-3")?.children).toHaveLength(0);
    });
  });

  describe("single schedule", () => {
    it("handles single schedule correctly", () => {
      renderScheduleList({ schedules: [mockSchedules[0]] });

      expect(screen.getByText("Daily PR Check")).toBeInTheDocument();
      expect(screen.queryByText("Weekday Updates")).not.toBeInTheDocument();
    });
  });
});
