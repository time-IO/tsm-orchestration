import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { defineComponent, h } from 'vue';

import IngestOverviewExternalApiTable from '@/components/IngestOverviewExternalApiTable.vue';
import type { IngestExternalApiRead } from '@/services/ingest_external_api/types';
import type { QTableRequestPropPagination } from '@/services/types';
import type { ColumnWidths } from '@/utils/overview_table_utils';
import { default_ingest_external_api_columns } from '@/utils/pagination_utils';

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

const OverviewTableStub = defineComponent({
  name: 'OverviewTable',
  props: [
    'rows',
    'loading',
    'columns',
    'storageKey',
    'columnWidths',
    'rowsPerPageOptions',
    'selectable',
    'pagination',
    'selected',
  ],
  emits: ['request', 'update:pagination', 'update:selected'],
  setup() {
    return () => h('div', { class: 'overview-table-stub' });
  },
});

const globalOptions = { stubs: { OverviewTable: OverviewTableStub } };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ROW = { id: 1, name: 'My external API' } as unknown as IngestExternalApiRead;

const PAGINATION: QTableRequestPropPagination = {
  page: 1,
  rowsPerPage: 10,
  sortBy: 'id',
  descending: false,
  rowsNumber: 0,
};

const mountTable = (props: Record<string, unknown> = {}) =>
  mount(IngestOverviewExternalApiTable, {
    props: { rows: [], loading: false, ...props },
    global: globalOptions,
  });

const getTable = (wrapper: ReturnType<typeof mountTable>) =>
  wrapper.findComponent(OverviewTableStub);

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('IngestOverviewExternalApiTable', () => {
  describe('initialization', () => {
    it('passes rows, loading and the table config to the overview table', () => {
      const table = getTable(mountTable({ rows: [ROW], loading: true }));

      expect(table.props('rows')).toEqual([ROW]);
      expect(table.props('loading')).toBe(true);
      expect(table.props('storageKey')).toBe('ingest-external-api');
      expect(table.props('columns')).toEqual(default_ingest_external_api_columns);
      expect(table.props('rowsPerPageOptions')).toEqual([10, 25, 50, 100, 200]);
      expect(table.props('selectable')).toBe(false);
    });

    it('passes custom columns, rows per page options and selectable', () => {
      const columns = [{ name: 'name', label: 'Name', field: 'name' }];
      const table = getTable(
        mountTable({ columns, rowsPerPageOptions: [5, 10], selectable: true }),
      );

      expect(table.props('columns')).toEqual(columns);
      expect(table.props('rowsPerPageOptions')).toEqual([5, 10]);
      expect(table.props('selectable')).toBe(true);
    });
  });

  describe('column widths', () => {
    it('defines a width for every default column', () => {
      const widths = getTable(mountTable()).props('columnWidths') as ColumnWidths;

      default_ingest_external_api_columns.forEach((col) => {
        expect(widths[col.name]?.default).toBeDefined();
      });
      expect(default_ingest_external_api_columns.map((c) => c.name)).not.toContain('action');
    });
  });

  describe('v-model:pagination', () => {
    it('passes the pagination to the overview table', () => {
      expect(getTable(mountTable({ pagination: PAGINATION })).props('pagination')).toEqual(
        PAGINATION,
      );
    });

    it('emits update:pagination when the overview table changes it', async () => {
      const wrapper = mountTable({ pagination: PAGINATION });
      const next = { ...PAGINATION, page: 2 };

      getTable(wrapper).vm.$emit('update:pagination', next);
      await wrapper.vm.$nextTick();

      expect(wrapper.emitted('update:pagination')?.at(-1)).toEqual([next]);
    });
  });

  describe('v-model:selected', () => {
    it('passes the selection to the overview table', () => {
      expect(getTable(mountTable({ selected: [ROW] })).props('selected')).toEqual([ROW]);
    });

    it('emits update:selected when the overview table changes it', async () => {
      const wrapper = mountTable({ selected: [] });

      getTable(wrapper).vm.$emit('update:selected', [ROW]);
      await wrapper.vm.$nextTick();

      expect(wrapper.emitted('update:selected')?.at(-1)).toEqual([[ROW]]);
    });
  });

  describe('request', () => {
    it('re-emits a request of the overview table as onRequest', async () => {
      const wrapper = mountTable();
      const payload = { pagination: PAGINATION };

      getTable(wrapper).vm.$emit('request', payload);
      await wrapper.vm.$nextTick();

      expect(wrapper.emitted('onRequest')).toEqual([[payload]]);
    });
  });
});
