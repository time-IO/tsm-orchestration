/**
 * Width constraints of an overview table column, as relative weights. The table converts them to
 * pixels by splitting its width among the visible columns in proportion to their `default` weights
 * (see `toPixelWidths`).
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

// in pixels, for columns without a configured `min`
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

/**
 * Converts relative width weights to pixels, so that the `default` weights of the given columns
 * add up to the available width.
 * @param widths - The width constraints of all columns, as relative weights
 * @param colNames - The columns sharing the available width
 * @param availableWidth - The width to split among these columns, in pixels
 * @returns The width constraints of all columns, in pixels
 */
export function toPixelWidths(
  widths: ColumnWidths,
  colNames: string[],
  availableWidth: number,
): ColumnWidths {
  const totalWeight = colNames.reduce((sum, c) => sum + (widths[c]?.default ?? 0), 0);
  const scale = totalWeight > 0 ? availableWidth / totalWeight : 0;
  return Object.fromEntries(
    Object.entries(widths).map(([colName, width]) => [
      colName,
      Object.fromEntries(Object.entries(width).map(([key, weight]) => [key, weight * scale])),
    ]),
  );
}

// tolerance for floating point comparisons of widths: half a pixel
export const WIDTH_EPSILON = 0.5;

/**
 * Sums the current widths of the given columns; columns without a width count as 0.
 * @param values - The current width per column
 * @param colNames - The columns to sum up
 * @returns The total width
 */
export function sumColumnWidths(values: ColumnWidthValues, colNames: string[]): number {
  return colNames.reduce((sum, c) => sum + (values[c] ?? 0), 0);
}

/**
 * Checks whether a column can still grow, i.e. it is below its maximum width.
 * @param widths - The width constraints of all columns
 * @param values - The current width per column
 * @param colName - The column name
 * @returns `true` if the column has a width and room to grow
 */
export function hasRoomToGrow(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  colName: string,
): boolean {
  const value = values[colName];
  return value !== undefined && value < maxWidthOf(widths, colName) - WIDTH_EPSILON;
}

/**
 * Checks whether a column can still shrink, i.e. it is above its minimum width.
 * @param widths - The width constraints of all columns
 * @param values - The current width per column
 * @param colName - The column name
 * @returns `true` if the column has a width and room to shrink
 */
export function hasRoomToShrink(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  colName: string,
): boolean {
  const value = values[colName];
  return value !== undefined && value > minWidthOf(widths, colName) + WIDTH_EPSILON;
}

/**
 * Sums up how much the given columns can shrink in total before reaching their minimum widths.
 * @param widths - The width constraints of all columns
 * @param values - The current width per column
 * @param colNames - The columns that may shrink
 * @returns The total shrinkable width; columns without a width are ignored
 */
export function shrinkableWidth(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  colNames: string[],
): number {
  return colNames.reduce((sum, c) => {
    const value = values[c];
    return value === undefined ? sum : sum + Math.max(0, value - minWidthOf(widths, c));
  }, 0);
}

/**
 * Spreads an amount of width evenly over the given columns, up to their maximum widths.
 * Width that no column can take any more is dropped.
 * @param widths - The width constraints of all columns
 * @param values - The current width per column
 * @param amount - The width to add, in pixels
 * @param receivers - The columns receiving the width; columns without a width are ignored
 * @returns The new width per column
 */
export function distributeWidth(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  amount: number,
  receivers: string[],
): ColumnWidthValues {
  const result = { ...values };
  const canGrow = (c: string) => hasRoomToGrow(widths, result, c);
  let remaining = amount;
  let candidates = receivers.filter(canGrow);
  while (remaining > WIDTH_EPSILON && candidates.length > 0) {
    const share = remaining / candidates.length;
    for (const c of candidates) {
      const give = Math.min(share, maxWidthOf(widths, c) - result[c]!);
      result[c] = result[c]! + give;
      remaining -= give;
    }
    candidates = candidates.filter(canGrow);
  }
  return result;
}

/**
 * Takes an amount of width evenly from the given columns, down to their minimum widths.
 * Width that no column can give any more is not taken.
 * @param widths - The width constraints of all columns
 * @param values - The current width per column
 * @param amount - The width to take, in pixels
 * @param donors - The columns giving the width; columns without a width are ignored
 * @returns The new width per column
 */
export function reclaimWidth(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  amount: number,
  donors: string[],
): ColumnWidthValues {
  const result = { ...values };
  const canShrink = (c: string) => hasRoomToShrink(widths, result, c);
  let remaining = amount;
  let candidates = donors.filter(canShrink);
  while (remaining > WIDTH_EPSILON && candidates.length > 0) {
    const share = remaining / candidates.length;
    for (const c of candidates) {
      const take = Math.min(share, result[c]! - minWidthOf(widths, c));
      result[c] = result[c]! - take;
      remaining -= take;
    }
    candidates = candidates.filter(canShrink);
  }
  return result;
}

/**
 * Scales the widths of the given columns proportionally so they add up to a target width.
 * Columns that would leave their minimum or maximum width are clamped to it, and the remaining
 * columns share the rest. If all columns are clamped, the target is not reached.
 * @param widths - The width constraints of all columns
 * @param values - The current width per column
 * @param colNames - The columns to scale; all of them must have a width
 * @param target - The total width to reach, in pixels
 * @returns The new width per column
 */
export function scaleColumnWidths(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  colNames: string[],
  target: number,
): ColumnWidthValues {
  const result = { ...values };
  let free = colNames;
  let remaining = target;
  while (free.length > 0) {
    const total = sumColumnWidths(result, free);
    if (total <= 0) break;
    const factor = remaining / total;
    const clamped = free.filter((c) => {
      const scaled = result[c]! * factor;
      return clampColumnWidth(widths, c, scaled) !== scaled;
    });
    if (clamped.length === 0) {
      free.forEach((c) => (result[c] = result[c]! * factor));
      break;
    }
    clamped.forEach((c) => {
      result[c] = clampColumnWidth(widths, c, result[c]! * factor);
      remaining -= result[c];
    });
    free = free.filter((c) => !clamped.includes(c));
  }
  return result;
}

/**
 * Fits the visible columns into the available width: fixed columns take their fixed width,
 * resizable columns without a width start with their default (or minimum), and all resizable
 * columns are then scaled proportionally to fill the rest.
 * @param widths - The width constraints of all columns, in pixels
 * @param values - The current width per column
 * @param colNames - The visible columns
 * @param availableWidth - The width to fill, in pixels
 * @returns The new width per column; fixed columns are not included
 */
export function fitColumnWidths(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  colNames: string[],
  availableWidth: number,
): ColumnWidthValues {
  const fixed = colNames.filter((c) => !isColumnResizable(widths, c));
  const resizable = colNames.filter((c) => isColumnResizable(widths, c));
  const result = Object.fromEntries(
    Object.entries(values).filter(([colName]) => !fixed.includes(colName)),
  );
  resizable.forEach((c) => {
    result[c] ??= widths[c]?.default ?? minWidthOf(widths, c);
  });
  const fixedWidth = fixed.reduce((sum, c) => sum + fixedWidthOf(widths, c), 0);
  return scaleColumnWidths(widths, result, resizable, availableWidth - fixedWidth);
}

/**
 * Resizes a column by dragging and keeps the total width: the other columns give or take the
 * difference evenly. The column cannot grow beyond what the others can give.
 * @param widths - The width constraints of all columns
 * @param startValues - The width per column when the drag started
 * @param colName - The dragged column
 * @param otherCols - The columns compensating the change
 * @param delta - The horizontal drag distance, in pixels
 * @returns The new width per column
 */
export function resizeColumn(
  widths: ColumnWidths,
  startValues: ColumnWidthValues,
  colName: string,
  otherCols: string[],
  delta: number,
): ColumnWidthValues {
  const startWidth = startValues[colName] ?? minWidthOf(widths, colName);
  const newWidth = Math.min(
    startWidth + shrinkableWidth(widths, startValues, otherCols),
    clampColumnWidth(widths, colName, startWidth + delta),
  );
  const result = { ...startValues, [colName]: newWidth };
  const widthDelta = newWidth - startWidth;
  return widthDelta > 0
    ? reclaimWidth(widths, result, widthDelta, otherCols)
    : distributeWidth(widths, result, -widthDelta, otherCols);
}

/**
 * Picks the column that takes up the remaining table width (rendered with `auto` width):
 * the last resizable column without a maximum width, or else the last resizable column.
 * @param widths - The width constraints of all columns
 * @param colNames - The visible columns, in display order
 * @returns The flexible column, or `undefined` if no column is resizable
 */
export function flexibleColumnOf(widths: ColumnWidths, colNames: string[]): string | undefined {
  const candidates = colNames.filter((c) => isColumnResizable(widths, c));
  return candidates.filter((c) => !hasMaxWidth(widths, c)).at(-1) ?? candidates.at(-1);
}

/**
 * Computes the minimum width of the table: fixed columns at their fixed width, the flexible
 * column at its minimum, and all other columns at their current (or minimum) width.
 * @param widths - The width constraints of all columns
 * @param values - The current width per column
 * @param colNames - The visible columns
 * @param flexibleColumn - The column rendered with `auto` width
 * @param extraWidth - Width of columns outside the constraints, e.g. a selection column
 * @returns The minimum table width, in pixels
 */
export function minTableWidthOf(
  widths: ColumnWidths,
  values: ColumnWidthValues,
  colNames: string[],
  flexibleColumn: string | undefined,
  extraWidth = 0,
): number {
  return colNames.reduce((sum, c) => {
    if (!isColumnResizable(widths, c)) return sum + fixedWidthOf(widths, c);
    if (c === flexibleColumn) return sum + minWidthOf(widths, c);
    return sum + (values[c] ?? minWidthOf(widths, c));
  }, extraWidth);
}
