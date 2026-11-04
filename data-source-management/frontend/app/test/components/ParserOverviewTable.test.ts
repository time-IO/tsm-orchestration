import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { mount } from '@vue/test-utils';
import { QBtn } from 'quasar';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';

import ParserOverviewTable from '@/components/ParserOverviewTable.vue'; // adjust path
import type { QTableRequestPropPagination } from '@/services/types';
import { default_parser_columns } from '@/utils/pagination_utils';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const { generatePathMock } = vi.hoisted(() => ({
  generatePathMock: vi.fn(
    (row: { id: number; parser_type: string }) => `/parser/${row.parser_type}/${row.id}`,
  ),
}));

// Keep the real column definition, only the path generation is replaced
vi.mock('@/utils/pagination_utils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/utils/pagination_utils')>();
  return { ...actual, generateParserPath: generatePathMock };
});

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

// Renders the scoped "actions" slot once per row, like the real table does
const OverviewTableStub = defineComponent({
  name: 'OverviewTable',
  props: [
    'rows',
    'loading',
    'columns',
    'storageKey',
    'colMinWidths',
    'defaultColWidths',
    'pagination',
  ],
  emits: ['update:pagination', 'request', 'delete'],
  setup:
    (props, { slots }) =>
    () =>
      h(
        'div',
        { class: 'overview-table-stub' },
        ((props.rows ?? []) as unknown[]).map((row) =>
          h('div', { class: 'row' }, slots.actions?.({ row })),
        ),
      ),
});

// QTooltip normally renders in a portal on hover only
const QTooltipStub = defineComponent({
  name: 'QTooltip',
  setup:
    (_, { slots }) =>
    () =>
      h('div', { class: 'tooltip' }, slots.default?.()),
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ROWS = [
  { id: 1, parser_type: 'csv' },
  { id: 2, parser_type: 'json' },
];

const PAGINATION = { page: 1, rowsPerPage: 25 } as QTableRequestPropPagination;

const mountParserOverviewTable = (props: Record<string, unknown> = {}) =>
  mount(ParserOverviewTable, {
    props: { rows: [], loading: false, ...props },
    global: { stubs: { OverviewTable: OverviewTableStub, QTooltip: QTooltipStub } },
  });

const getTable = (w: ReturnType<typeof mountParserOverviewTable>) =>
  w.findComponent(OverviewTableStub);

const setWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', { configurable: true, writable: true, value: width });
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ParserOverviewTable', () => {
  const originalWidth = window.innerWidth;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    setWindowWidth(originalWidth);
  });

  describe('initialization and props', () => {
    it('passes rows and loading to the table', () => {
      const w = mountParserOverviewTable({ rows: ROWS, loading: true });

      expect(getTable(w).props('rows')).toEqual(ROWS);
      expect(getTable(w).props('loading')).toBe(true);
    });

    it('updates the table when rows and loading change', async () => {
      const w = mountParserOverviewTable({ rows: ROWS, loading: true });

      await w.setProps({ rows: [ROWS[0]], loading: false });

      expect(getTable(w).props('rows')).toEqual([ROWS[0]]);
      expect(getTable(w).props('loading')).toBe(false);
    });

    it('passes the parser columns and the storage key', () => {
      const w = mountParserOverviewTable();

      expect(getTable(w).props('columns')).toEqual(default_parser_columns);
      expect(getTable(w).props('storageKey')).toBe('parser');
    });

    it('defines min and default widths for the same columns', () => {
      const w = mountParserOverviewTable();
      const minKeys = Object.keys(getTable(w).props('colMinWidths') as object).sort();
      const defaultKeys = Object.keys(getTable(w).props('defaultColWidths') as object).sort();

      expect(minKeys.length).toBeGreaterThan(0);
      expect(defaultKeys).toEqual(minKeys);
    });
  });

  describe('default column widths by window size', () => {
    it.each([
      ['below 1200px', 1199, { permission_group: 80, name: 80, uuid: 80 }],
      ['from 1200px', 1200, { permission_group: 150, name: 120, uuid: 120 }],
    ])('uses the matching widths %s', (_label, width, expected) => {
      setWindowWidth(width);

      const w = mountParserOverviewTable();

      expect(getTable(w).props('defaultColWidths')).toMatchObject(expected);
    });
  });

  describe('pagination (v-model)', () => {
    it('passes the pagination to the table and follows changes from outside', async () => {
      const w = mountParserOverviewTable({ pagination: PAGINATION });
      expect(getTable(w).props('pagination')).toEqual(PAGINATION);

      const next = { page: 3, rowsPerPage: 50 } as QTableRequestPropPagination;
      await w.setProps({ pagination: next });

      expect(getTable(w).props('pagination')).toEqual(next);
    });

    it('emits update:pagination when the table changes the pagination', () => {
      const w = mountParserOverviewTable({ pagination: PAGINATION });
      const next = { page: 2, rowsPerPage: 25 };

      getTable(w).vm.$emit('update:pagination', next);

      expect(w.emitted('update:pagination')).toEqual([[next]]);
    });
  });

  describe('events', () => {
    it('emits onRequest with the request payload of the table', () => {
      const w = mountParserOverviewTable();
      const payload = {
        pagination: { page: 2, rowsPerPage: 10, sortBy: 'name', descending: false },
      };

      getTable(w).vm.$emit('request', payload);

      expect(w.emitted('onRequest')).toEqual([[payload]]);
    });

    it.each([[5], [null]])('emits delete with id %s and closes the dialog', (id) => {
      const w = mountParserOverviewTable();
      const closeDialog = vi.fn();

      getTable(w).vm.$emit('delete', id, closeDialog);

      expect(w.emitted('delete')).toEqual([[id]]);
      expect(closeDialog).toHaveBeenCalledTimes(1);
    });

    it('emits delete before it closes the dialog', () => {
      const calls: string[] = [];
      const w = mountParserOverviewTable({ onDelete: () => calls.push('delete') });

      getTable(w).vm.$emit('delete', 5, () => calls.push('closeDialog'));

      expect(calls).toEqual(['delete', 'closeDialog']);
    });
  });

  describe('row actions', () => {
    it('renders view, edit and copy buttons per row with the matching routes', () => {
      const w = mountParserOverviewTable({ rows: ROWS });
      const btns = w.findAllComponents(QBtn);

      expect(btns.map((b) => b.props('to'))).toEqual([
        '/parser/csv/1',
        '/parser/csv/1/edit',
        '/parser/csv/1/copy',
        '/parser/json/2',
        '/parser/json/2/edit',
        '/parser/json/2/copy',
      ]);
    });

    it('builds the base path from the row', () => {
      mountParserOverviewTable({ rows: ROWS });

      expect(generatePathMock).toHaveBeenCalledWith(ROWS[0]);
      expect(generatePathMock).toHaveBeenCalledWith(ROWS[1]);
    });

    it('renders no action buttons without rows', () => {
      const w = mountParserOverviewTable({ rows: [] });

      expect(w.findAllComponents(QBtn)).toHaveLength(0);
    });

    it('uses the expected icons and tooltips', () => {
      const w = mountParserOverviewTable({ rows: [ROWS[0]] });
      const btns = w.findAllComponents(QBtn);

      expect(btns.map((b) => b.props('icon'))).toEqual(['visibility', 'edit', 'content_copy']);
      expect(btns[0]!.text()).toContain('View details');
      expect(btns[1]!.text()).toContain('Edit');
      expect(btns[2]!.text()).toContain('Copy parser');
    });
  });
});
