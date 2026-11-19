import { describe, expect, it, vi } from 'vitest';
import { fetchAllPages } from '@/utils/pagination_utils';

function pagedSource(total: number) {
  const all = Array.from({ length: total }, (_, i) => i);
  return vi.fn(async (page: number, size: number) => ({
    items: all.slice((page - 1) * size, page * size),
    total,
    page,
    size,
    pages: Math.ceil(total / size),
  }));
}

describe('fetchAllPages', () => {
  it('collects items across all pages', async () => {
    const fetchPage = pagedSource(5);
    expect(await fetchAllPages(fetchPage, 2)).toEqual([0, 1, 2, 3, 4]);
    expect(fetchPage.mock.calls).toEqual([
      [1, 2],
      [2, 2],
      [3, 2],
    ]);
  });

  it('stops after a full last page once the total is reached', async () => {
    const fetchPage = pagedSource(4);
    expect(await fetchAllPages(fetchPage, 2)).toEqual([0, 1, 2, 3]);
    expect(fetchPage).toHaveBeenCalledTimes(2);
  });

  it('stops on a short page even if the total is inconsistent', async () => {
    const fetchPage = vi.fn(async () => ({ items: [1], total: 10, page: 1, size: 2, pages: 5 }));
    expect(await fetchAllPages(fetchPage, 2)).toEqual([1]);
    expect(fetchPage).toHaveBeenCalledOnce();
  });
});
