import { isIsoDate } from '@/utils/validation/validators';

/**
 * Truncates a string to the specified length.
 * @param text - The original string
 * @param maxLength - Maximum length of the truncated string
 * @param breakOnWord - If true, truncates only at word boundaries (spaces)
 * @param suffix - Suffix to append to the truncated string (default: "...")
 * @returns The truncated string
 */
export function truncateText(
  text: string,
  maxLength: number,
  breakOnWord = false,
  suffix = '...',
): string {
  if (!text || text.length <= maxLength) return text;

  if (breakOnWord) {
    const truncated = text.slice(0, maxLength + 1);
    const lastSpace = truncated.lastIndexOf(' ');
    if (lastSpace > 0) {
      return truncated.slice(0, lastSpace) + suffix;
    }
  }

  return text.slice(0, maxLength) + suffix;
}

/**
 * Stringifies any value of unknown type. Includes parsing of ISO dates.
 * @param value - The value to stringify string
 * @returns The parsed string
 */
export function unknownToString(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') {
    return String(value);
  }

  if (typeof value === 'string') {
    const date = new Date(value);
    if (!Number.isNaN(date.getTime()) && isIsoDate(value)) {
      return new Intl.DateTimeFormat('de-DE', {
        dateStyle: 'medium',
        timeStyle: 'medium',
      }).format(date);
    }
    return value;
  }

  return JSON.stringify(value) ?? '';
}

/**
 * Converts the given input to a number or null.
 * If the input is an empty string or null, the method returns null.
 * Otherwise, it converts the input to a number.
 *
 * @param {string | number | null} value - The value to be converted to a nullable number.
 * @return {number | null} The converted number, or null if the input is an empty string or null.
 */
export function toNullableNumber(value: string | number | null): number | null {
  return value === '' || value === null ? null : Number(value);
}

/**
 * Parses a JSON field from the provided value. If the value is already an object, it gets returned as is.
 * If the value is invalid or cannot be parsed into JSON, it throws an error.
 *
 * @param {string | object | null} value - The value to be parsed, which could be a JSON string or an object.
 * @return {object | null} The parsed JSON object or null if the input is falsy.
 * @throws {Error} Throws an error if the value cannot be parsed as JSON.
 */
export function parseJsonField(
  value: string | Record<string, unknown> | null | undefined,
): Record<string, unknown> | null {
  if (!value) return null;
  if (typeof value === 'object') return value;

  try {
    const parsed: unknown = JSON.parse(value);
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      throw new Error();
    }
    return parsed as Record<string, unknown>;
  } catch {
    throw new Error('Pandas read csv must contain a valid JSON object');
  }
}
