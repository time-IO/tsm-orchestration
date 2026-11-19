/**
 * Width constraints of an overview table column, all in pixels.
 * - `min`: the column cannot be resized below this width
 * - `max`: the column cannot be resized above this width
 * - `default`: the initial width; without one, the column starts with `auto` width
 * A column with equal values for `min` and `max` has a fixed width and is not resizable.
 */
export interface ColumnWidth {
  min?: number;
  max?: number;
  default?: number;
}

export type ColumnWidths = Record<string, ColumnWidth>;

export const DEFAULT_MIN_COLUMN_WIDTH = 50;

/**
 * Returns the minimum width of a column.
 * @param widths - The width constraints of all columns
 * @param colName - The column name
 * @returns The configured minimum, or `DEFAULT_MIN_COLUMN_WIDTH`
 */
export function minWidthOf(widths: ColumnWidths, colName: string): number {
  return widths[colName]?.min ?? DEFAULT_MIN_COLUMN_WIDTH;
}

/**
 * Returns the maximum width of a column.
 * @param widths - The width constraints of all columns
 * @param colName - The column name
 * @returns The configured maximum, or `Infinity`
 */
export function maxWidthOf(widths: ColumnWidths, colName: string): number {
  return widths[colName]?.max ?? Infinity;
}

/**
 * Checks whether a column has a maximum width.
 * @param widths - The width constraints of all columns
 * @param colName - The column name
 * @returns `true` if a `max` is configured
 */
export function hasMaxWidth(widths: ColumnWidths, colName: string): boolean {
  return widths[colName]?.max !== undefined;
}

/**
 * Checks whether a column can be resized, i.e. it does not have a fixed width (`min === max`).
 * @param widths - The width constraints of all columns
 * @param colName - The column name
 * @returns `true` if the column is resizable
 */
export function isColumnResizable(widths: ColumnWidths, colName: string): boolean {
  return minWidthOf(widths, colName) < maxWidthOf(widths, colName);
}

/**
 * Returns the width of a non-resizable column.
 * @param widths - The width constraints of all columns
 * @param colName - The column name
 * @returns The configured default, or its minimum width
 */
export function fixedWidthOf(widths: ColumnWidths, colName: string): number {
  return widths[colName]?.default ?? minWidthOf(widths, colName);
}

/**
 * Clamps a width to the minimum and maximum width of a column.
 * @param widths - The width constraints of all columns
 * @param colName - The column name
 * @param width - The width to clamp
 * @returns The clamped width
 */
export function clampColumnWidth(widths: ColumnWidths, colName: string, width: number): number {
  return Math.min(maxWidthOf(widths, colName), Math.max(minWidthOf(widths, colName), width));
}

/**
 * Collects the default widths of all columns that have one.
 * @param widths - The width constraints of all columns
 * @returns The default width per column name
 */
export function defaultColumnWidths(widths: ColumnWidths): Record<string, number> {
  return Object.fromEntries(
    Object.entries(widths)
      .filter(([, width]) => width.default !== undefined)
      .map(([colName, width]) => [colName, width.default!]),
  );
}

/** Current width per column name, in pixels. */
export type ColumnWidthValues = Record<string, number>;
