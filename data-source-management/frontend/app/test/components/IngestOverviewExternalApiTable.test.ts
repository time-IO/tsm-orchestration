// test/components/IngestExternalApiOverviewTable.test.ts
import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { QCheckbox, QItem, QTable } from 'quasar';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick } from 'vue';

import IngestExternalApiOverviewTable from '@/components/IngestOverviewExternalApiTable.vue'; // adjust path

// Fixed columns, so the tests do not depend on the real column definition
const { COLUMNS } = vi.hoisted(() => ({
  COLUMNS: [
    { name: 'id', label: 'ID', field: 'id' },
    { name: 'permission_group', label: 'Permission Group', field: 'permission_group' },
    { name: 'name', label: 'Name', field: 'name' },
    { name: 'uuid', label: 'UUID', field: 'uuid' },
    { name: 'created_at', label: 'Created at', field: 'created_at' },
    { name: 'action', label: 'Action', field: 'action' },
  ],
}));

vi.mock('@/utils/pagination_utils', () => ({
  default_ingest_external_api_columns: COLUMNS,
}));

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Constants, stubs & helpers
// ---------------------------------------------------------------------------

const COL_WIDTHS_KEY = 'ingestExtApi-col-widths';
const VISIBLE_COLUMNS_KEY = 'ingestExtApi-visible-columns';

const ALL_NAMES = COLUMNS.map((c) => c.name);
const OPTION_COLUMNS = COLUMNS.filter((c) => c.name !== 'action');

const PAGINATION = { page: 1, rowsPerPage: 10, sortBy: 'id', descending: false, rowsNumber: 0 };

// QMenu renders into a teleport and only after a click. The stub renders the content inline.
const QMenuStub = defineComponent({
  name: 'QMenu',
  setup:
    (_, { slots }) =>
    () =>
      h('div', { class: 'q-menu-stub' }, slots.default?.()),
});

const mountTable = (props: Record<string, unknown> = {}, attrs: Record<string, unknown> = {}) =>
  mount(IngestExternalApiOverviewTable, {
    props: { rows: [], loading: false, ...props },
    attrs,
    global: { stubs: { QMenu: QMenuStub } },
  });

const getTable = (wrapper: VueWrapper) => wrapper.findComponent(QTable);

const visibleColumnsOf = (wrapper: VueWrapper) => getTable(wrapper).props('visibleColumns');

const labelOf = (name: string) => {
  const col = COLUMNS.find((c) => c.name === name);
  if (!col) throw new Error(`Column "${name}" not found`);
  return col.label;
};

const headerLabels = (wrapper: VueWrapper) => wrapper.findAll('th').map((th) => th.text());

const headerCell = (wrapper: VueWrapper, name: string) => {
  const label = labelOf(name);
  const cell = wrapper.findAll('th').find((th) => th.text() === label);
  if (!cell) throw new Error(`Header cell "${label}" not found`);
  return cell;
};

const widthOf = (wrapper: VueWrapper, name: string) =>
  headerCell(wrapper, name).element.style.width;

const menuItem = (wrapper: VueWrapper, label: string) => {
  const item = wrapper.findAllComponents(QItem).find((i) => i.text() === label);
  if (!item) throw new Error(`Menu item "${label}" not found`);
  return item;
};

const isChecked = (item: ReturnType<typeof menuItem>) =>
  item.findComponent(QCheckbox).props('modelValue');

const setWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true, writable: true });
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('IngestExternalApiOverviewTable', () => {
  const originalWidth = window.innerWidth;

  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setWindowWidth(originalWidth);
    // consumes a click listener that a resize may have left on the document
    document.dispatchEvent(new MouseEvent('click'));
  });

  describe('initialization', () => {
    it('passes rows, loading and the default columns to the table', () => {
      const rows = [{ id: 1, name: 'First' }];

      const wrapper = mountTable({ rows, loading: true });

      expect(getTable(wrapper).props('rows')).toEqual(rows);
      expect(getTable(wrapper).props('loading')).toBe(true);
      expect(getTable(wrapper).props('columns')).toEqual(COLUMNS);
    });

    it('passes custom columns to the table', () => {
      const custom = [{ name: 'id', label: 'ID', field: 'id' }];

      const wrapper = mountTable({ columns: custom });

      expect(getTable(wrapper).props('columns')).toEqual(custom);
    });

    it('requests the first page once after mounting', async () => {
      const wrapper = mountTable({ pagination: PAGINATION });

      await flushPromises();

      const calls = wrapper.emitted('onRequest');
      expect(calls).toHaveLength(1);
      expect(calls?.[0]?.[0]).toMatchObject({ pagination: { page: 1, rowsPerPage: 10 } });
    });

    it('shows all columns by default', () => {
      const wrapper = mountTable();

      expect(visibleColumnsOf(wrapper)).toEqual(ALL_NAMES);
      expect(headerLabels(wrapper)).toEqual(COLUMNS.map((c) => c.label));
    });

    it('renders cell values and N/A for empty values', () => {
      const wrapper = mountTable({ rows: [{ id: 1, name: 'First', uuid: '', created_at: null }] });

      const cells = wrapper.findAll('td').map((td) => td.text());

      expect(cells).toContain('First');
      // every column except id and name has no value in this row
      expect(cells.filter((c) => c === 'N/A')).toHaveLength(COLUMNS.length - 2);
    });
  });

  describe('attributes', () => {
    it('forwards attributes to the table instead of the root element', () => {
      const wrapper = mountTable({}, { title: 'My table' });

      expect(getTable(wrapper).props('title')).toBe('My table');
      expect(wrapper.attributes('title')).toBeUndefined();
    });
  });

  describe('v-model:pagination', () => {
    it('passes the pagination to the table', () => {
      const wrapper = mountTable({ pagination: PAGINATION });

      expect(getTable(wrapper).props('pagination')).toMatchObject(PAGINATION);
    });

    it('emits update:pagination when the table changes it', async () => {
      const wrapper = mountTable({ pagination: PAGINATION });
      await flushPromises(); // consume the emit from the initial requestServerInteraction
      const next = { ...PAGINATION, page: 2 };

      getTable(wrapper).vm.$emit('update:pagination', next);

      const calls = wrapper.emitted('update:pagination') ?? [];
      expect(calls[calls.length - 1]).toEqual([next]);
    });
  });

  describe('request', () => {
    it('re-emits a table request as onRequest with the same payload', async () => {
      const wrapper = mountTable();
      await flushPromises(); // consume the initial request
      const payload = { pagination: { ...PAGINATION, page: 3 }, filter: undefined };

      getTable(wrapper).vm.$emit('request', payload);

      const calls = wrapper.emitted('onRequest') ?? [];
      expect(calls[calls.length - 1]).toEqual([payload]);
    });
  });

  describe('column visibility menu', () => {
    it('lists every column except action', () => {
      const wrapper = mountTable();

      const labels = wrapper
        .findAllComponents(QItem)
        .map((i) => i.text())
        .filter((t) => t !== 'All');

      expect(labels).toEqual(OPTION_COLUMNS.map((c) => c.label));
    });

    it('shows every option and the all-option as checked by default', () => {
      const wrapper = mountTable();

      expect(isChecked(menuItem(wrapper, 'All'))).toBe(true);
      for (const col of OPTION_COLUMNS) {
        expect(isChecked(menuItem(wrapper, col.label)), col.name).toBe(true);
      }
    });

    it('hides a column when its menu item is clicked', async () => {
      const wrapper = mountTable();

      await menuItem(wrapper, labelOf('name')).trigger('click');

      expect(visibleColumnsOf(wrapper)).not.toContain('name');
      expect(headerLabels(wrapper)).not.toContain('Name');
      expect(isChecked(menuItem(wrapper, 'Name'))).toBe(false);
      expect(isChecked(menuItem(wrapper, 'All'))).toBe(false);
    });

    it('shows the column again when its menu item is clicked twice', async () => {
      const wrapper = mountTable();

      await menuItem(wrapper, 'Name').trigger('click');
      await menuItem(wrapper, 'Name').trigger('click');

      expect(visibleColumnsOf(wrapper)).toContain('name');
      expect(headerLabels(wrapper)).toContain('Name');
      expect(isChecked(menuItem(wrapper, 'All'))).toBe(true);
    });

    it('toggles a column via its checkbox as well', async () => {
      const wrapper = mountTable();

      menuItem(wrapper, 'Name').findComponent(QCheckbox).vm.$emit('update:modelValue', false);
      await nextTick();

      expect(visibleColumnsOf(wrapper)).not.toContain('name');
    });

    it('hides everything except action via "All" when all columns are visible', async () => {
      const wrapper = mountTable();

      await menuItem(wrapper, 'All').trigger('click');

      expect(visibleColumnsOf(wrapper)).toEqual(['action']);
      expect(headerLabels(wrapper)).toEqual(['Action']);
      expect(isChecked(menuItem(wrapper, 'All'))).toBe(false);
    });

    it('shows all columns via "All" when some are hidden', async () => {
      const wrapper = mountTable();
      await menuItem(wrapper, 'Name').trigger('click');

      await menuItem(wrapper, 'All').trigger('click');

      expect(visibleColumnsOf(wrapper)).toEqual(ALL_NAMES);
      expect(isChecked(menuItem(wrapper, 'All'))).toBe(true);
    });

    it('saves the visible columns in sessionStorage', async () => {
      const wrapper = mountTable();

      await menuItem(wrapper, 'Name').trigger('click');

      expect(JSON.parse(sessionStorage.getItem(VISIBLE_COLUMNS_KEY) ?? 'null')).toEqual(
        visibleColumnsOf(wrapper),
      );
    });

    it('restores the saved visible columns on mount', () => {
      sessionStorage.setItem(VISIBLE_COLUMNS_KEY, JSON.stringify(['id']));

      const wrapper = mountTable();

      expect(visibleColumnsOf(wrapper)).toEqual(['id']);
      expect(headerLabels(wrapper)).toEqual(['ID']);
    });
  });

  describe('default column widths', () => {
    it('uses the wide widths on large windows', () => {
      setWindowWidth(1400);

      const wrapper = mountTable();

      expect(widthOf(wrapper, 'id')).toBe('60px');
      expect(widthOf(wrapper, 'permission_group')).toBe('150px');
      expect(widthOf(wrapper, 'name')).toBe('120px');
      expect(widthOf(wrapper, 'uuid')).toBe('120px');
      expect(widthOf(wrapper, 'created_at')).toBe('110px');
    });

    it('uses the narrow widths on small windows', () => {
      setWindowWidth(1000);

      const wrapper = mountTable();

      expect(widthOf(wrapper, 'permission_group')).toBe('80px');
      expect(widthOf(wrapper, 'name')).toBe('80px');
      expect(widthOf(wrapper, 'uuid')).toBe('80px');
    });

    it('restores saved column widths on mount', () => {
      sessionStorage.setItem(COL_WIDTHS_KEY, JSON.stringify({ id: '200px' }));

      const wrapper = mountTable();

      expect(widthOf(wrapper, 'id')).toBe('200px');
    });
  });

  describe('column resize', () => {
    const startDrag = async (wrapper: VueWrapper, x: number) => {
      await headerCell(wrapper, 'id')
        .find('.col-resize-handle')
        .trigger('mousedown', { clientX: x });
    };

    const move = async (x: number) => {
      document.dispatchEvent(new MouseEvent('mousemove', { clientX: x }));
      await nextTick();
    };

    beforeEach(() => {
      // jsdom has no layout, so the start width of the header cell is fixed here
      vi.spyOn(HTMLElement.prototype, 'offsetWidth', 'get').mockReturnValue(100);
    });

    it('changes the width by the dragged distance', async () => {
      const wrapper = mountTable();

      await startDrag(wrapper, 100);
      await move(150);

      expect(widthOf(wrapper, 'id')).toBe('150px');
    });

    it('does not shrink below the minimum width', async () => {
      const wrapper = mountTable();

      await startDrag(wrapper, 100);
      await move(-400);

      // minimum width of the id column
      expect(widthOf(wrapper, 'id')).toBe('40px');
    });

    it('saves the widths in sessionStorage on mouseup only', async () => {
      const wrapper = mountTable();

      await startDrag(wrapper, 100);
      await move(150);
      expect(sessionStorage.getItem(COL_WIDTHS_KEY)).toBeNull();

      document.dispatchEvent(new MouseEvent('mouseup'));

      expect(JSON.parse(sessionStorage.getItem(COL_WIDTHS_KEY) ?? '{}').id).toBe('150px');
    });

    it('stops resizing after mouseup', async () => {
      const wrapper = mountTable();

      await startDrag(wrapper, 100);
      await move(150);
      document.dispatchEvent(new MouseEvent('mouseup'));
      await move(300);

      expect(widthOf(wrapper, 'id')).toBe('150px');
    });

    it('swallows the next click so the column is not sorted after a resize', async () => {
      const wrapper = mountTable();
      const onClick = vi.fn();
      document.body.addEventListener('click', onClick);

      await startDrag(wrapper, 100);
      document.dispatchEvent(new MouseEvent('mouseup'));
      document.body.click(); // swallowed
      document.body.click(); // the listener removed itself, this one goes through
      document.body.removeEventListener('click', onClick);

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('uses 50px as minimum width for columns without a configured minimum', async () => {
      const wrapper = mountTable();

      await headerCell(wrapper, 'action').find('.col-resize-handle').trigger('mousedown', { clientX: 100 });
      await move(-400);

      expect(widthOf(wrapper, 'action')).toBe('50px');
    });

    it('falls back to the stored width when the handle is not inside a th', async () => {
      const wrapper = mountTable();
      const handle = headerCell(wrapper, 'id').find('.col-resize-handle');
      vi.spyOn(handle.element, 'closest').mockReturnValue(null);

      await handle.trigger('mousedown', { clientX: 100 });
      await move(150);

      // stored width of id is 60px, plus the dragged 50px
      expect(widthOf(wrapper, 'id')).toBe('110px');
    });

    it('falls back to 100px when the column has no stored width and no th', async () => {
      const wrapper = mountTable();
      const handle = headerCell(wrapper, 'action').find('.col-resize-handle');
      vi.spyOn(handle.element, 'closest').mockReturnValue(null);

      await handle.trigger('mousedown', { clientX: 100 });
      await move(150);

      expect(widthOf(wrapper, 'action')).toBe('150px');
    });
  });

  describe('selection', () => {
    it('shows a header checkbox only for multiple selection', () => {
      const rows = [{ id: 1 }];

      const multiple = mountTable({ rows }, { selection: 'multiple' });
      const single = mountTable({ rows }, { selection: 'single' });

      expect(multiple.find('thead').findComponent(QCheckbox).exists()).toBe(true);
      expect(single.find('thead').findComponent(QCheckbox).exists()).toBe(false);
    });

    it.for([
      { selection: 'multiple', expected: true },
      { selection: 'single', expected: true },
      { selection: undefined, expected: false },
    ])('row checkbox exists: $expected for selection $selection', (testCase) => {
        const wrapper = mountTable({ rows: [{ id: 1 }] }, { selection: testCase.selection });

        expect(wrapper.find('tbody').findComponent(QCheckbox).exists()).toBe(testCase.expected);
    });
  });

  describe('cell tooltip', () => {
    it('renders the cell value as tooltip content', () => {
      const wrapper = mount(IngestExternalApiOverviewTable, {
        props: { rows: [{ id: 1, name: 'First' }], loading: false },
        global: {
          stubs: {
            QMenu: QMenuStub,
            QTooltip: { template: '<i class="tooltip"><slot/></i>' },
          },
        },
      });

      expect(wrapper.findAll('tbody .tooltip').map((t) => t.text())).toEqual(['1', 'First']);
    });
  });

  describe('cell content', () => {
    it('renders a value for a column without a configured width', () => {
      const wrapper = mountTable({ rows: [{ id: 1, action: 'open' }] });

      const cells = wrapper.findAll('tbody td').map((td) => td.text());

      expect(cells).toContain('open');
    });
  });
});
