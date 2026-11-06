// Converts a cron expression to a human-readable string.
//
// Supports standard 5-field cron format: minute hour day-of-month month day-of-week
//
// Examples:
// - "0 9 * * 1-5" → "Weekdays at 9:00 AM"
// - "0 9 * * *" → "Daily at 9:00 AM"
// - "30 14 * * *" → "Daily at 2:30 PM"
// - "0 */2 * * *" → "Every 2 hours"
// - "0 0 1 * *" → "Monthly on day 1 at 12:00 AM"
export function cronToHumanReadable(cronExpression: string): string {
  const parts = cronExpression.trim().split(/\s+/);

  if (parts.length !== 5) {
    return cronExpression; // Return as-is if not standard format
  }

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

  // Format time from hour and minute
  const formatTime = (h: string, m: string): string => {
    if (h.startsWith("*/")) {
      return ""; // Will be handled separately
    }
    const hourNum = parseInt(h, 10);
    const minuteNum = parseInt(m, 10);
    if (isNaN(hourNum) || isNaN(minuteNum)) {
      return "";
    }
    const period = hourNum >= 12 ? "PM" : "AM";
    const displayHour = hourNum === 0 ? 12 : hourNum > 12 ? hourNum - 12 : hourNum;
    const displayMinute = minuteNum.toString().padStart(2, "0");
    return `${displayHour}:${displayMinute} ${period}`;
  };

  // Check for "every N hours" pattern
  if (hour.startsWith("*/")) {
    const interval = hour.slice(2);
    if (minute === "0") {
      return `Every ${interval} hours`;
    }
    return `Every ${interval} hours at minute ${minute}`;
  }

  // Check for "every N minutes" pattern
  if (minute.startsWith("*/")) {
    const interval = minute.slice(2);
    return `Every ${interval} minutes`;
  }

  const time = formatTime(hour, minute);
  if (!time) {
    return cronExpression; // Cannot parse, return as-is
  }

  // Specific day of month (e.g., "0 9 1 * *" = monthly on day 1)
  if (dayOfMonth !== "*" && month === "*" && dayOfWeek === "*") {
    return `Monthly on day ${dayOfMonth} at ${time}`;
  }

  // Specific month and day
  if (dayOfMonth !== "*" && month !== "*") {
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    const monthNum = parseInt(month, 10);
    const monthName = monthNames[monthNum - 1] || month;
    return `${monthName} ${dayOfMonth} at ${time}`;
  }

  // Weekday patterns
  if (dayOfWeek !== "*") {
    const weekdayDescription = parseWeekdays(dayOfWeek);
    if (weekdayDescription) {
      return `${weekdayDescription} at ${time}`;
    }
  }

  // Daily (all wildcards except time)
  if (dayOfMonth === "*" && month === "*" && dayOfWeek === "*") {
    return `Daily at ${time}`;
  }

  return cronExpression;
}

/**
 * Parse day-of-week field into human-readable description
 */
function parseWeekdays(dayOfWeek: string): string | null {
  const dayNames: Record<string, string> = {
    "0": "Sunday",
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
    "7": "Sunday", // Some cron implementations use 7 for Sunday
  };

  const shortDayNames: Record<string, string> = {
    "0": "Sun",
    "1": "Mon",
    "2": "Tue",
    "3": "Wed",
    "4": "Thu",
    "5": "Fri",
    "6": "Sat",
    "7": "Sun",
  };

  // Common patterns
  if (dayOfWeek === "1-5" || dayOfWeek === "MON-FRI") {
    return "Weekdays";
  }
  if (dayOfWeek === "0,6" || dayOfWeek === "6,0" || dayOfWeek === "SAT,SUN" || dayOfWeek === "SUN,SAT") {
    return "Weekends";
  }

  // Range pattern (e.g., "1-5")
  const rangeMatch = dayOfWeek.match(/^(\d)-(\d)$/);
  if (rangeMatch) {
    const start = shortDayNames[rangeMatch[1]];
    const end = shortDayNames[rangeMatch[2]];
    if (start && end) {
      return `${start}-${end}`;
    }
  }

  // Single day
  if (dayNames[dayOfWeek]) {
    return `Every ${dayNames[dayOfWeek]}`;
  }

  // List of days (e.g., "1,3,5")
  const days = dayOfWeek.split(",");
  if (days.length > 1 && days.every(d => dayNames[d])) {
    const dayNameList = days.map(d => shortDayNames[d]);
    return dayNameList.join(", ");
  }

  return null;
}
