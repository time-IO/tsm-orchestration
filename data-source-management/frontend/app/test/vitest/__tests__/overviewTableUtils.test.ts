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
  toPixelWidths,
  distributeWidth,
  fitColumnWidths,
  flexibleColumnOf,
  hasRoomToGrow,
  hasRoomToShrink,
  minTableWidthOf,
  reclaimWidth,
  resizeColumn,
  scaleColumnWidths,
  shrinkableWidth,
  sumColumnWidths,
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

describe('toPixelWidths', () => {
  it('splits the available width by the default weights of the given columns', () => {
    const pixels = toPixelWidths(widths, ['id', 'action'], 1000);

    expect(pixels.id).toEqual({ min: 200, default: 300 });
    expect(pixels.action).toEqual({ min: 700, max: 700, default: 700 });
    expect(pixels.name).toEqual({ min: 500, max: 1500 });
    expect(pixels.empty).toEqual({});
  });

  it('ignores columns without a default weight', () => {
    const pixels = toPixelWidths(widths, ['id', 'name'], 600);

    expect(pixels.id?.default).toBe(600);
  });

  it('scales to zero without any default weight', () => {
    expect(toPixelWidths(widths, ['name'], 600).name).toEqual({ min: 0, max: 0 });
  });
});

// pixel constraints for the layout calculations
const px: ColumnWidths = {
  a: { min: 50, max: 300, default: 100 },
  b: { min: 50, default: 100 },
  c: { min: 100, default: 200 },
  fixed: { min: 80, max: 80, default: 80 },
};

describe('sumColumnWidths', () => {
  it('sums the widths and counts missing ones as 0', () => {
    expect(sumColumnWidths({ a: 100, b: 50 }, ['a', 'b', 'c'])).toBe(150);
  });
});

describe('hasRoomToGrow / hasRoomToShrink', () => {
  it('compares against the maximum and minimum width', () => {
    expect(hasRoomToGrow(px, { a: 300 }, 'a')).toBe(false);
    expect(hasRoomToGrow(px, { a: 299 }, 'a')).toBe(true);
    expect(hasRoomToShrink(px, { a: 50 }, 'a')).toBe(false);
    expect(hasRoomToShrink(px, { a: 51 }, 'a')).toBe(true);
  });

  it('is false for columns without a width', () => {
    expect(hasRoomToGrow(px, {}, 'a')).toBe(false);
    expect(hasRoomToShrink(px, {}, 'a')).toBe(false);
  });
});

describe('shrinkableWidth', () => {
  it('sums the width above the minimum of each column', () => {
    expect(shrinkableWidth(px, { a: 100, b: 40, c: 150 }, ['a', 'b', 'c', 'missing'])).toBe(100);
  });
});

describe('distributeWidth', () => {
  it('spreads the width evenly and respects maximum widths', () => {
    const values = { a: 280, b: 100 };

    expect(distributeWidth(px, values, 100, ['a', 'b'])).toEqual({ a: 300, b: 180 });
    expect(values).toEqual({ a: 280, b: 100 });
  });

  it('ignores columns without a width', () => {
    expect(distributeWidth(px, { b: 100 }, 50, ['a', 'b'])).toEqual({ b: 150 });
  });
});

describe('reclaimWidth', () => {
  it('takes the width evenly and respects minimum widths', () => {
    expect(reclaimWidth(px, { a: 60, b: 200 }, 100, ['a', 'b'])).toEqual({ a: 50, b: 110 });
  });

  it('takes no more than the columns can give', () => {
    expect(reclaimWidth(px, { a: 60, b: 60 }, 100, ['a', 'b'])).toEqual({ a: 50, b: 50 });
  });
});

describe('scaleColumnWidths', () => {
  it('scales the widths proportionally to the target', () => {
    expect(scaleColumnWidths(px, { b: 100, c: 300 }, ['b', 'c'], 800)).toEqual({ b: 200, c: 600 });
  });

  it('clamps columns at their limits and lets the others share the rest', () => {
    const result = scaleColumnWidths(px, { a: 200, b: 200 }, ['a', 'b'], 1000);

    expect(result).toEqual({ a: 300, b: 700 });
  });

  it('stops at the minimum widths when the target is too small', () => {
    expect(scaleColumnWidths(px, { b: 100, c: 200 }, ['b', 'c'], 30)).toEqual({ b: 50, c: 100 });
  });
});

describe('fitColumnWidths', () => {
  it('fills the available width and drops fixed columns from the values', () => {
    const result = fitColumnWidths(px, { fixed: 120, b: 100 }, ['b', 'c', 'fixed'], 680);

    expect(result.fixed).toBeUndefined();
    expect(sumColumnWidths(result, ['b', 'c']) + 80).toBeCloseTo(680);
  });

  it('starts columns without a width at their default', () => {
    expect(fitColumnWidths(px, {}, ['b', 'c'], 600)).toEqual({ b: 200, c: 400 });
  });
});

describe('resizeColumn', () => {
  const start = { a: 100, b: 100, c: 200 };

  it('grows a column and takes the width from the others', () => {
    expect(resizeColumn(px, start, 'a', ['b', 'c'], 60)).toEqual({ a: 160, b: 70, c: 170 });
  });

  it('shrinks a column and gives the width to the others', () => {
    expect(resizeColumn(px, start, 'a', ['b', 'c'], -40)).toEqual({ a: 60, b: 120, c: 220 });
  });

  it('stops at the minimum width of the dragged column', () => {
    expect(resizeColumn(px, start, 'a', ['b', 'c'], -500).a).toBe(50);
  });

  it('cannot grow beyond what the others can give', () => {
    expect(resizeColumn(px, start, 'b', ['c'], 500)).toEqual({ a: 100, b: 200, c: 100 });
  });
});

describe('flexibleColumnOf', () => {
  it('picks the last resizable column without a maximum width', () => {
    expect(flexibleColumnOf(px, ['b', 'c', 'a', 'fixed'])).toBe('c');
  });

  it('falls back to the last resizable column', () => {
    expect(flexibleColumnOf(px, ['a', 'fixed'])).toBe('a');
    expect(flexibleColumnOf(px, ['fixed'])).toBeUndefined();
  });
});

describe('minTableWidthOf', () => {
  it('counts fixed, flexible and other columns differently', () => {
    expect(minTableWidthOf(px, { a: 150, c: 400 }, ['a', 'b', 'c', 'fixed'], 'c', 64)).toBe(
      64 + 150 + 50 + 100 + 80,
    );
  });
});
