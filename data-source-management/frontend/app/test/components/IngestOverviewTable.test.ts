// test/components/IngestOverviewTable.test.ts
import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { mount } from '@vue/test-utils';
import { QBtn } from 'quasar';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';

import IngestOverviewTable from '@/components/IngestOverviewTable.vue'; // adjust path

vi.mock('@/utils/pagination_utils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/utils/pagination_utils')>();
  return {
    ...actual,
    generateIngestPath: (row: { id: number }) => `/ingests/${row.id}`,
    formatExternalApiType: (type: string) => `fmt(${type})`,
  };
});

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

type Row = Record<string, unknown>;

// The slot "value-tooltip" needs a column, which the real table would provide
let tooltipCol: Row = { name: 'name', value: 'x' };

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
    'tableStyle',
  ],
  emits: ['request', 'delete', 'update:pagination'],
  setup(props, { slots }) {
    return () =>
      h(
        'div',
        { class: 'overview-table-stub' },
        (props.rows as Row[]).flatMap((row) => [
          h('div', { class: 'actions' }, slots.actions?.({ row })),
          h('span', { class: 'tooltip' }, slots['value-tooltip']?.({ col: tooltipCol, row })),
        ]),
      );
  },
});

// QBtn is stubbed so "to" does not need a router; the stub keeps the props
const globalOptions = {
  stubs: { OverviewTable: OverviewTableStub, QBtn: true, QTooltip: true },
  renderStubDefaultSlot: true,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ROW = { id: 1, uuid: 'abc-123', name: 'My ingest' };

const PAGINATION = {
  page: 1,
  rowsPerPage: 10,
  sortBy: 'id',
  descending: false,
  rowsNumber: 0,
};

const mountTable = (props: Record<string, unknown> = {}) =>
  mount(IngestOverviewTable, {
    props: { rows: [], loading: false, ...props },
    global: globalOptions,
  });

const getTable = (wrapper: ReturnType<typeof mountTable>) =>
  wrapper.findComponent(OverviewTableStub);

const getActionBtn = (wrapper: ReturnType<typeof mountTable>, icon: string) => {
  const btn = wrapper.findAllComponents(QBtn).find((b) => b.props('icon') === icon);
  if (!btn) throw new Error(`QBtn with icon "${icon}" not found`);
  return btn;
};

const setWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true, writable: true });
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('IngestOverviewTable', () => {
  const originalWidth = window.innerWidth;

  afterEach(() => {
    setWindowWidth(originalWidth);
    tooltipCol = { name: 'name', value: 'x' };
  });

  describe('initialization', () => {
    it('passes rows, loading and the fixed table config to the overview table', () => {
      const wrapper = mountTable({ rows: [ROW], loading: true });
      const table = getTable(wrapper);

      expect(table.props('rows')).toEqual([ROW]);
      expect(table.props('loading')).toBe(true);
      expect(table.props('storageKey')).toBe('ingest');
      expect(table.props('tableStyle')).toBe('table-layout: fixed; width: 100%');
      expect(table.props('columns')).toBeDefined();
    });

    it('uses the wide default column widths on large windows', () => {
      setWindowWidth(1400);

      const widths = getTable(mountTable()).props('defaultColWidths');

      expect(widths).toMatchObject({ permission_group: 150, name: 120, uuid: 120 });
    });

    it('uses the narrow default column widths on small windows', () => {
      setWindowWidth(1000);

      const widths = getTable(mountTable()).props('defaultColWidths');

      expect(widths).toMatchObject({ permission_group: 80, name: 80, uuid: 80 });
    });

    it('passes the same minimum widths regardless of the window size', () => {
      setWindowWidth(1000);
      const small = getTable(mountTable()).props('colMinWidths');
      setWindowWidth(1400);
      const large = getTable(mountTable()).props('colMinWidths');

      expect(small).toEqual(large);
      expect(small).toMatchObject({ uuid: 80, action: 120 });
    });
  });

  describe('prop changes', () => {
    it('forwards changed rows and loading to the overview table', async () => {
      const wrapper = mountTable({ rows: [], loading: false });

      await wrapper.setProps({ rows: [ROW], loading: true });

      expect(getTable(wrapper).props('rows')).toEqual([ROW]);
      expect(getTable(wrapper).props('loading')).toBe(true);
    });
  });

  describe('v-model:pagination', () => {
    it('passes the pagination to the overview table', () => {
      const wrapper = mountTable({ pagination: PAGINATION });

      expect(getTable(wrapper).props('pagination')).toEqual(PAGINATION);
    });

    it('emits update:pagination when the overview table changes it', async () => {
      const wrapper = mountTable({ pagination: PAGINATION });
      const next = { ...PAGINATION, page: 2 };

      getTable(wrapper).vm.$emit('update:pagination', next);

      expect(wrapper.emitted('update:pagination')).toEqual([[next]]);
    });
  });

  describe('events', () => {
    it('re-emits request as onRequest with the same payload', () => {
      const wrapper = mountTable();
      const payload = { pagination: PAGINATION, filter: undefined };

      getTable(wrapper).vm.$emit('request', payload);

      expect(wrapper.emitted('onRequest')).toEqual([[payload]]);
    });

    it('emits delete with the id and closes the dialog', () => {
      const wrapper = mountTable();
      const closeDialog = vi.fn();

      getTable(wrapper).vm.$emit('delete', 5, closeDialog);

      expect(wrapper.emitted('delete')).toEqual([[5]]);
      expect(closeDialog).toHaveBeenCalledTimes(1);
    });

    it('also handles a delete without id', () => {
      const wrapper = mountTable();
      const closeDialog = vi.fn();

      getTable(wrapper).vm.$emit('delete', null, closeDialog);

      expect(wrapper.emitted('delete')).toEqual([[null]]);
      expect(closeDialog).toHaveBeenCalledTimes(1);
    });
  });

  describe('actions slot', () => {
    it('links view, edit and copy to the ingest path of the row', () => {
      const wrapper = mountTable({ rows: [ROW] });

      expect(getActionBtn(wrapper, 'visibility').props('to')).toBe('/ingests/1');
      expect(getActionBtn(wrapper, 'edit').props('to')).toBe('/ingests/1/edit');
      expect(getActionBtn(wrapper, 'content_copy').props('to')).toBe('/ingests/1/copy');
    });

    it('builds the visualization link from the uuid', () => {
      const wrapper = mountTable({ rows: [ROW] });

      const btn = getActionBtn(wrapper, 'img:icons/grafana_icon.png');

      expect(btn.props('href')).toBe(`${window.location.origin}/visualization/d/abc-123?orgId=1`);
      expect(btn.props('target')).toBe('_blank');
    });

    it('url-encodes the uuid in the visualization link', () => {
      const wrapper = mountTable({ rows: [{ ...ROW, uuid: 'a b/c' }] });

      expect(getActionBtn(wrapper, 'img:icons/grafana_icon.png').props('href')).toBe(
        `${window.location.origin}/visualization/d/a%20b%2Fc?orgId=1`,
      );
    });

    it('uses an empty visualization link when the row has no uuid', () => {
      const wrapper = mountTable({ rows: [{ ...ROW, uuid: null }] });

      expect(getActionBtn(wrapper, 'img:icons/grafana_icon.png').props('href')).toBe('');
    });
  });

  describe('value-tooltip slot', () => {
    it('appends the formatted external api type for the ingest_type column', () => {
      tooltipCol = { name: 'ingest_type', value: 'api' };

      const wrapper = mountTable({ rows: [{ ...ROW, external_api_type: 'zentra' }] });

      expect(wrapper.find('.tooltip').text()).toBe('api – fmt(zentra)');
    });

    it('shows only the value for the ingest_type column without external api type', () => {
      tooltipCol = { name: 'ingest_type', value: 'sftp' };

      const wrapper = mountTable({ rows: [{ ...ROW, external_api_type: null }] });

      expect(wrapper.find('.tooltip').text()).toBe('sftp');
    });

    it('shows only the value for other columns, even with external api type', () => {
      tooltipCol = { name: 'name', value: 'My ingest' };

      const wrapper = mountTable({ rows: [{ ...ROW, external_api_type: 'zentra' }] });

      expect(wrapper.find('.tooltip').text()).toBe('My ingest');
    });
  });
});
