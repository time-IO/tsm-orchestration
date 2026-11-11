import { i18n } from '@/boot/i18n';
import { isIsoDate } from '@/utils/validation/validators';

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
 * Converts a value to a Date if it is an ISO timestamp.
 *
 * @param value - Any value, e.g. "2024-01-01T12:00:00Z"
 * @returns The Date, or null if the value is not a valid ISO timestamp
 */
export function parseIsoTimestamp(value: unknown): Date | null {
  if (typeof value !== 'string' || !isIsoDate(value)) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

const dateFormats = new Map<string | undefined, Intl.DateTimeFormat>();

function getDateFormat(timeZone?: string): Intl.DateTimeFormat {
  let format = dateFormats.get(timeZone);
  if (!format) {
    format = new Intl.DateTimeFormat('en-US', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hourCycle: 'h23',
      timeZoneName: 'longOffset',
    });
    dateFormats.set(timeZone, format);
  }
  return format;
}

/**
 * Formats a date as "YYYY-MM-DD HH:mm:ss +/-HH:MM".
 *
 * @param date - The date to format
 * @param timeZone - An IANA timezone (e.g. "Europe/Berlin"), defaults to the browser's timezone
 * @returns The formatted date (e.g. "2024-01-01 13:00:00 +01:00" in Europe/Berlin)
 */
export function formatDate(date: Date, timeZone?: string): string {
  const parts = Object.fromEntries(
    getDateFormat(timeZone)
      .formatToParts(date)
      .map((part) => [part.type, part.value]),
  );
  // "longOffset" yields e. g. "GMT+01:00", or just "GMT" for UTC
  const offset = parts.timeZoneName?.replace('GMT', '') || '+00:00';
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second} ${offset}`;
}
