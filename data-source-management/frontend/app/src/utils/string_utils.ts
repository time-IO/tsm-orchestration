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
 * Removes a prefix from a string if it is present.
 * @param text - The original string
 * @param prefix - Prefix to remove (e.g. "https://")
 * @param caseSensitive - If false, the prefix is matched ignoring case (default: true)
 * @returns The string without the leading prefix, or the original string if it does not start with it
 */
export function removePrefixIfExists(text: string, prefix: string, caseSensitive = true): string {
  if (!text || !prefix) return text;
  const haystack = caseSensitive ? text : text.trim().toLowerCase();
  const needle = caseSensitive ? prefix : prefix.toLowerCase();
  return haystack.startsWith(needle) ? text.slice(prefix.length) : text;
}

/**
 * Removes a suffix from a string if it is present.
 * @param text - The original string
 * @param suffix - Suffix to remove (e.g. "/")
 * @param caseSensitive - If false, the suffix is matched ignoring case (default: true)
 * @returns The string without the trailing suffix, or the original string if it does not end with it
 */
export function removeSuffixIfExists(text: string, suffix: string, caseSensitive = true): string {
  if (!text || !suffix) return text;
  const haystack = caseSensitive ? text : text.trim().toLowerCase();
  const needle = caseSensitive ? suffix : suffix.toLowerCase();
  return haystack.endsWith(needle) ? text.slice(0, text.length - suffix.length) : text;
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
