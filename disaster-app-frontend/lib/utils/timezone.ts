/**
 * Format date/time in Mumbai (Asia/Kolkata) timezone
 */
export function formatMumbaiTime(date: Date): string {
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    timeZone: 'Asia/Kolkata'
  };

  const formatter = new Intl.DateTimeFormat('en-IN', options);
  return formatter.format(date);
}

/**
 * Generate chat title with Mumbai timezone
 */
export function generateChatTitle(): string {
  const formatted = formatMumbaiTime(new Date());
  return `Disaster Chat ${formatted}`;
}

/**
 * Get current time in Mumbai timezone as ISO string equivalent
 */
export function getMumbaiTime(): Date {
  const now = new Date();
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'Asia/Kolkata'
  };

  const formatter = new Intl.DateTimeFormat('en-CA', options);
  const parts = formatter.formatToParts(now);
  
  const dateObj: any = {};
  parts.forEach(part => {
    dateObj[part.type] = part.value;
  });

  return new Date(`${dateObj.year}-${dateObj.month}-${dateObj.day}T${dateObj.hour}:${dateObj.minute}:${dateObj.second}`);
}
