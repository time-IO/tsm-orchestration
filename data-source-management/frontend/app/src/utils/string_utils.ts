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
