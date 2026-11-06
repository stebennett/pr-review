import { describe, it, expect } from "vitest";
import { cronToHumanReadable } from "./cron";

describe("cronToHumanReadable", () => {
  describe("daily schedules", () => {
    it("converts daily at 9am", () => {
      expect(cronToHumanReadable("0 9 * * *")).toBe("Daily at 9:00 AM");
    });

    it("converts daily at 2:30pm", () => {
      expect(cronToHumanReadable("30 14 * * *")).toBe("Daily at 2:30 PM");
    });

    it("converts daily at midnight", () => {
      expect(cronToHumanReadable("0 0 * * *")).toBe("Daily at 12:00 AM");
    });

    it("converts daily at noon", () => {
      expect(cronToHumanReadable("0 12 * * *")).toBe("Daily at 12:00 PM");
    });

    it("converts daily at 11pm", () => {
      expect(cronToHumanReadable("0 23 * * *")).toBe("Daily at 11:00 PM");
    });
  });

  describe("weekday schedules", () => {
    it("converts weekdays at 9am (1-5 format)", () => {
      expect(cronToHumanReadable("0 9 * * 1-5")).toBe("Weekdays at 9:00 AM");
    });

    it("converts weekends", () => {
      expect(cronToHumanReadable("0 10 * * 0,6")).toBe("Weekends at 10:00 AM");
    });

    it("converts specific day range", () => {
      expect(cronToHumanReadable("0 9 * * 2-4")).toBe("Tue-Thu at 9:00 AM");
    });

    it("converts single day (Monday)", () => {
      expect(cronToHumanReadable("0 9 * * 1")).toBe("Every Monday at 9:00 AM");
    });

    it("converts single day (Sunday with 0)", () => {
      expect(cronToHumanReadable("0 9 * * 0")).toBe("Every Sunday at 9:00 AM");
    });

    it("converts list of days", () => {
      expect(cronToHumanReadable("0 9 * * 1,3,5")).toBe("Mon, Wed, Fri at 9:00 AM");
    });
  });

  describe("monthly schedules", () => {
    it("converts monthly on day 1", () => {
      expect(cronToHumanReadable("0 9 1 * *")).toBe("Monthly on day 1 at 9:00 AM");
    });

    it("converts monthly on day 15", () => {
      expect(cronToHumanReadable("0 0 15 * *")).toBe("Monthly on day 15 at 12:00 AM");
    });
  });

  describe("interval schedules", () => {
    it("converts every 2 hours", () => {
      expect(cronToHumanReadable("0 */2 * * *")).toBe("Every 2 hours");
    });

    it("converts every 6 hours", () => {
      expect(cronToHumanReadable("0 */6 * * *")).toBe("Every 6 hours");
    });

    it("converts every 15 minutes", () => {
      expect(cronToHumanReadable("*/15 * * * *")).toBe("Every 15 minutes");
    });

    it("converts every 30 minutes", () => {
      expect(cronToHumanReadable("*/30 * * * *")).toBe("Every 30 minutes");
    });
  });

  describe("specific date schedules", () => {
    it("converts specific month and day", () => {
      expect(cronToHumanReadable("0 9 25 12 *")).toBe("December 25 at 9:00 AM");
    });

    it("converts January 1st", () => {
      expect(cronToHumanReadable("0 0 1 1 *")).toBe("January 1 at 12:00 AM");
    });
  });

  describe("edge cases", () => {
    it("returns original for invalid cron (too few parts)", () => {
      expect(cronToHumanReadable("0 9 * *")).toBe("0 9 * *");
    });

    it("returns original for invalid cron (too many parts)", () => {
      expect(cronToHumanReadable("0 9 * * * *")).toBe("0 9 * * * *");
    });

    it("handles extra whitespace", () => {
      expect(cronToHumanReadable("  0   9   *   *   *  ")).toBe("Daily at 9:00 AM");
    });

    it("returns original for unparseable expressions", () => {
      expect(cronToHumanReadable("abc def ghi jkl mno")).toBe("abc def ghi jkl mno");
    });
  });
});
