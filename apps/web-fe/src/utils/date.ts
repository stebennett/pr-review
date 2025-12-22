import { formatDistanceToNow, parseISO } from "date-fns";

/**
 * Formats a date as relative time (e.g., "3 days ago")
 */
export function formatRelativeTime(date: Date | string): string {
  const dateObj = typeof date === "string" ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true });
}
