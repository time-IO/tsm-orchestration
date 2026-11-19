import { describe, expect, it } from 'vitest';
import {
  clampColumnWidth,
  DEFAULT_MIN_COLUMN_WIDTH,
  defaultColumnWidths,
  fixedWidthOf,
  hasMaxWidth,
  isColumnResizable,
  maxWidthOf,
  minWidthOf,
  type ColumnWidths,
} from '@/utils/overview_table_utils';

const widths: ColumnWidths = {
  id: { min: 40, default: 60 },
  name: { min: 100, max: 300 },
  action: { min: 140, max: 140, default: 140 },
  empty: {},
};

describe('minWidthOf / maxWidthOf', () => {
  it('returns the configured values', () => {
    expect(minWidthOf(widths, 'name')).toBe(100);
    expect(maxWidthOf(widths, 'name')).toBe(300);
  });

  it('falls back for missing values and columns', () => {
    expect(minWidthOf(widths, 'empty')).toBe(DEFAULT_MIN_COLUMN_WIDTH);
    expect(minWidthOf(widths, 'unknown')).toBe(DEFAULT_MIN_COLUMN_WIDTH);
    expect(maxWidthOf(widths, 'id')).toBe(Infinity);
  });
});

describe('hasMaxWidth', () => {
  it('detects a configured max', () => {
    expect(hasMaxWidth(widths, 'name')).toBe(true);
    expect(hasMaxWidth(widths, 'id')).toBe(false);
  });
});

describe('isColumnResizable', () => {
  it('is false for fixed columns', () => {
    expect(isColumnResizable(widths, 'action')).toBe(false);
  });

  it('is true for other columns', () => {
    expect(isColumnResizable(widths, 'id')).toBe(true);
    expect(isColumnResizable(widths, 'name')).toBe(true);
    expect(isColumnResizable(widths, 'unknown')).toBe(true);
  });
});

describe('fixedWidthOf', () => {
  it('prefers the default and falls back to the min', () => {
    expect(fixedWidthOf(widths, 'action')).toBe(140);
    expect(fixedWidthOf(widths, 'name')).toBe(100);
  });
});

describe('clampColumnWidth', () => {
  it('clamps to min and max', () => {
    expect(clampColumnWidth(widths, 'name', 50)).toBe(100);
    expect(clampColumnWidth(widths, 'name', 500)).toBe(300);
    expect(clampColumnWidth(widths, 'name', 200)).toBe(200);
    expect(clampColumnWidth(widths, 'id', 5000)).toBe(5000);
  });
});

describe('defaultColumnWidths', () => {
  it('collects only columns with a default', () => {
    expect(defaultColumnWidths(widths)).toEqual({ id: 60, action: 140 });
  });
});
