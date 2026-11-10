import { i18n } from '@/boot/i18n';

const tPath = 'time';

/**
Formats a given duration in milliseconds into an *exact* time string.
 *
 * Returns a human-readable, localized string representing the precise duration
 * (up to minutes), such as:
 * - "2 days, 4 hours, 12 minutes"
 * - "1 hour, 5 minutes"
 *
 * The returned string is already formatted using the i18n templates from `utils/time.ts`.
 *
 * @param milliseconds - The duration in milliseconds.
 * @returns {string} A localized, formatted string (e.g. "2 days, 4 hours, 12 minutes").
 */
export function formatExact(milliseconds: number): string {
  const MS_PER_MINUTE = 60 * 1000;
  const MS_PER_HOUR = 60 * MS_PER_MINUTE;
  const MS_PER_DAY = 24 * MS_PER_HOUR;

  const days = Math.floor(milliseconds / MS_PER_DAY);
  const hours = Math.floor((milliseconds % MS_PER_DAY) / MS_PER_HOUR);
  const minutes = Math.floor((milliseconds % MS_PER_HOUR) / MS_PER_MINUTE);

  const parts: string[] = [];
  if (days > 0) parts.push(i18n.global.t(`${tPath}.exact.days`, { count: days }));
  if (hours > 0) parts.push(i18n.global.t(`${tPath}.exact.hours`, { count: hours }));
  if (minutes > 0 || parts.length === 0)
    parts.push(i18n.global.t(`${tPath}.exact.minutes`, { count: minutes }));

  return parts.join(', ');
}

/**
 * Formats a given duration in milliseconds into an *approximate* time string.
 *
 * Returns a rough, localized time estimate, rounded to the largest appropriate unit,
 * such as:
 * - "almost 3 days"
 * - "about 1 hour"
 *
 * The returned string is already formatted using the i18n templates from `utils/time.ts`.
 *
 * @param milliseconds - The duration in milliseconds.
 * @returns {string} A localized, formatted string (e.g. "almost 3 days").
 */
export function formatApprox(milliseconds: number): string {
  const MS_PER_MINUTE = 60 * 1000;
  const MS_PER_HOUR = 60 * MS_PER_MINUTE;
  const MS_PER_DAY = 24 * MS_PER_HOUR;

  const days = milliseconds / MS_PER_DAY;
  const hours = milliseconds / MS_PER_HOUR;
  const minutes = milliseconds / MS_PER_MINUTE;

  let count: number;
  let unit: 'day' | 'hour' | 'minute';
  let prefixKey: string;

  if (days >= 1) {
    count = Math.round(days);
    unit = 'day';
    prefixKey = days < count ? 'almost' : 'about';
  } else if (hours >= 1) {
    count = Math.round(hours);
    unit = 'hour';
    prefixKey = hours < count ? 'almost' : 'about';
  } else {
    count = Math.round(minutes);
    unit = 'minute';
    prefixKey = minutes < count ? 'almost' : 'about';
  }

  const prefix = i18n.global.t(`${tPath}.approximate.${prefixKey}`, { count, unit });
  const unitLabel = i18n.global.t(`${tPath}.approximate.units.${unit}`, { count });

  return prefix.replace('{unit}', unitLabel);
}

/**
 * Formats an ISO timestamp as "YYYY-MM-DD HH:mm:ss +/-HH:MM" in the browser's timezone.
 *
 * @param isoString - The ISO timestamp (e.g. "2024-01-01T12:00:00Z")
 * @returns The timestamp converted to the browser's timezone
 *   (e.g. "2024-01-01 13:00:00 +01:00" in Europe/Berlin)
 */
export function formatIsoTimestampAsLocal(isoString: string): string {
  const date = new Date(isoString);

  const pad = (num: number) => String(num).padStart(2, '0');

  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());

  const tzOffsetMinutes = -date.getTimezoneOffset();
  const sign = tzOffsetMinutes >= 0 ? '+' : '-';
  const absOffset = Math.abs(tzOffsetMinutes);
  const tzHours = pad(Math.floor(absOffset / 60));
  const tzMinutes = pad(absOffset % 60);

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} ${sign}${tzHours}:${tzMinutes}`;
}

/**
 * Formats an ISO timestamp as "YYYY-MM-DD HH:mm:ss +/-HH:MM", keeping its own time and UTC offset.
 *
 * @param isoString - The ISO timestamp (e.g. "2024-01-01T12:00:00+01:00")
 * @returns The formatted timestamp (e.g. "2024-01-01 12:00:00 +01:00")
 */
export function formatIsoTimestamp(isoString: string): string {
  return isoString
    .replace('T', ' ')
    .replace(/(Z|[+-]\d{2}:\d{2})$/, (offset) => ` ${offset === 'Z' ? '+00:00' : offset}`);
}
