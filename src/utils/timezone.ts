/**
 * Timezone utility for converting timestamps to Indian Standard Time (IST).
 */

const IST_OFFSET = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30 in milliseconds

/**
 * Convert a date to IST and format it.
 */
export function toIST(date: Date | string | null | undefined): string {
  if (!date) return "";
  
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  // Get UTC time in milliseconds
  const utcTime = d.getTime();
  
  // Add IST offset (UTC+5:30)
  const istTime = new Date(utcTime + IST_OFFSET);
  
  return istTime.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

/**
 * Format a date in IST with custom format.
 */
export function formatIST(
  date: Date | string | null | undefined,
  format: "short" | "long" | "datetime" | "date" = "datetime"
): string {
  if (!date) return "";
  
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  const options: Intl.DateTimeFormatOptions = {
    timeZone: "Asia/Kolkata",
  };
  
  switch (format) {
    case "short":
      options.year = "numeric";
      options.month = "short";
      options.day = "numeric";
      break;
    case "long":
      options.year = "numeric";
      options.month = "long";
      options.day = "numeric";
      options.hour = "2-digit";
      options.minute = "2-digit";
      break;
    case "date":
      options.year = "numeric";
      options.month = "2-digit";
      options.day = "2-digit";
      break;
    case "datetime":
    default:
      options.year = "numeric";
      options.month = "2-digit";
      options.day = "2-digit";
      options.hour = "2-digit";
      options.minute = "2-digit";
      options.second = "2-digit";
      options.hour12 = false;
      break;
  }
  
  return d.toLocaleString("en-IN", options);
}

/**
 * Get relative time in IST (e.g., "2 hours ago").
 */
export function relativeTimeIST(date: Date | string | null | undefined): string {
  if (!date) return "";
  
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) return "just now";
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  
  return formatIST(d, "short");
}

