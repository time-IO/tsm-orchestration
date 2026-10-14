import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { QSelect } from 'quasar';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import PermissionGroupSelect from '@/components/PermissionGroupSelect.vue';
import type { PermissionGroup } from '@/services/permission_group/types';

const { dispatchGetListMock, notifyMock } = vi.hoisted(() => ({
  dispatchGetListMock: vi.fn(),
  notifyMock: vi.fn(),
}));

vi.mock('@/stores/permissionGroupStore', () => ({
  usePermissionGroupStore: () => ({ dispatchGetList: dispatchGetListMock }),
}));

vi.mock('quasar', async (importOriginal) => {
  const actual = await importOriginal<typeof import('quasar')>();
  return {
    ...actual,
    useQuasar: () => ({ notify: notifyMock }),
  };
});

installQuasarPlugin();

const PAGE_SIZE = 50;

const makeGroups = (count: number, startId = 1): PermissionGroup[] =>
  Array.from({ length: count }, (_, i) => ({
    id: startId + i,
    name: `group-${startId + i}: Name ${startId + i}`,
    uuid: `uuid-${startId + i}`,
  }));

const makeGroup = (id: number, name: string): PermissionGroup => ({
  id,
  name,
  uuid: `uuid-${id}`,
});

const mountSelect = async (
  props: {
    modelValue?: unknown;
    label?: string;
    rules?: Array<(val: unknown) => string | boolean>;
    preselectedItem?: PermissionGroup | null;
  } = {},
) => {
  const wrapper = mount(PermissionGroupSelect, { props });
  await flushPromises();
  return wrapper;
};

const getSelect = (wrapper: Awaited<ReturnType<typeof mountSelect>>) =>
  wrapper.findComponent(QSelect);

const getOptions = (wrapper: Awaited<ReturnType<typeof mountSelect>>) =>
  getSelect(wrapper).props('options') as PermissionGroup[];

describe('PermissionGroupSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dispatchGetListMock.mockReset();
    dispatchGetListMock.mockResolvedValue({ total: 2, items: makeGroups(2) });
  });

  describe('loading', () => {
    it('fetches the first page with the page size on mount', async () => {
      await mountSelect();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(1);
      expect(dispatchGetListMock).toHaveBeenCalledWith(1, PAGE_SIZE);
    });

    it('passes the fetched items as options to the select', async () => {
      const wrapper = await mountSelect();

      expect(getOptions(wrapper).map((o) => o.id)).toEqual([1, 2]);
    });

    it('notifies and keeps the options empty when fetching fails', async () => {
      dispatchGetListMock.mockRejectedValue(new Error('network'));

      const wrapper = await mountSelect();

      expect(notifyMock).toHaveBeenCalledTimes(1);
      expect(notifyMock).toHaveBeenCalledWith({
        position: 'top',
        type: 'negative',
        message: 'Failed to fetch permission groups',
      });
      expect(getOptions(wrapper)).toEqual([]);
    });
  });

  describe('props and v-model', () => {
    it('uses the default label without a label prop', async () => {
      const wrapper = await mountSelect();

      expect(getSelect(wrapper).props('label')).toBe('Permission Group *');
    });

    it('passes the rules to the select', async () => {
      const rule = (val: unknown) => !!val || 'Permission Group is required';

      const wrapper = await mountSelect({ rules: [rule] });

      expect(getSelect(wrapper).props('rules')).toEqual([rule]);
    });

    it('passes the modelValue to the select and updates it on prop change', async () => {
      const wrapper = await mountSelect({ modelValue: 1 });
      expect(getSelect(wrapper).props('modelValue')).toBe(1);

      await wrapper.setProps({ modelValue: 2 });

      expect(getSelect(wrapper).props('modelValue')).toBe(2);
    });

    it('emits update:modelValue when the select changes', async () => {
      const wrapper = await mountSelect();

      getSelect(wrapper).vm.$emit('update:modelValue', 2);

      expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([2]);
    });
  });

  describe('option label', () => {
    it.for([
      { name: 'Group A: Sensors', expected: 'Sensors' },
      { name: 'Group A:   Sensors', expected: 'Sensors' },
      { name: 'No prefix', expected: 'No prefix' },
      { name: 'a: b: c', expected: 'b: c' },
    ])('renders "$name" as  "$expected"', async (testCase) => {
      const wrapper = await mountSelect();
      const optionLabel = getSelect(wrapper).props('optionLabel') as (opt: unknown) => string;

      expect(optionLabel({ id: 1, name: testCase.name })).toBe(testCase.expected);
    });
  });

  describe('filtering', () => {
    const emitFilter = (wrapper: Awaited<ReturnType<typeof mountSelect>>, val: string) => {
      const update = vi.fn((cb: () => void) => cb());
      getSelect(wrapper).vm.$emit('filter', val, update);
      return update;
    };

    beforeEach(() => {
      dispatchGetListMock.mockResolvedValue({
        total: 3,
        items: [
          makeGroup(1, 'UFZ: Alpha'),
          makeGroup(2, 'UFZ: Beta'),
          makeGroup(3, 'Other: alphabet'),
        ],
      });
    });

    it('filters the options case-insensitively by name', async () => {
      const wrapper = await mountSelect();

      const update = emitFilter(wrapper, 'ALPHA');
      await wrapper.vm.$nextTick();

      expect(update).toHaveBeenCalledTimes(1);
      expect(getOptions(wrapper).map((o) => o.id)).toEqual([1, 3]);
    });

    it('shows all options again for an empty search term', async () => {
      const wrapper = await mountSelect();
      emitFilter(wrapper, 'beta');
      await wrapper.vm.$nextTick();
      expect(getOptions(wrapper)).toHaveLength(1);

      emitFilter(wrapper, '');
      await wrapper.vm.$nextTick();

      expect(getOptions(wrapper)).toHaveLength(3);
    });

    it('shows no options when nothing matches', async () => {
      const wrapper = await mountSelect();

      emitFilter(wrapper, 'does_not_exist');
      await wrapper.vm.$nextTick();

      expect(getOptions(wrapper)).toEqual([]);
    });
  });

  describe('preselectedItem', () => {
    it('adds a missing preselected item to the options', async () => {
      const wrapper = await mountSelect();
      const extra = makeGroup(99, 'Extra: Group');

      await wrapper.setProps({ preselectedItem: extra });

      expect(getOptions(wrapper).map((o) => o.id)).toEqual([1, 2, 99]);
    });

    it('does not add a preselected item that is already in the options', async () => {
      const wrapper = await mountSelect();
      const existing = getOptions(wrapper)[0]!;

      await wrapper.setProps({ preselectedItem: { ...existing } });

      expect(getOptions(wrapper).map((o) => o.id)).toEqual([1, 2]);
    });
  });

  describe('pagination via virtual scroll', () => {
    const scroll = (
      wrapper: Awaited<ReturnType<typeof mountSelect>>,
      to: number,
      refresh = vi.fn(),
    ) => {
      getSelect(wrapper).vm.$emit('virtual-scroll', { to, ref: { refresh } });
      return refresh;
    };

    beforeEach(() => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeGroups(PAGE_SIZE, 1) });
    });

    it('fetches the next page near the end of the list and appends the items', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeGroups(10, 51) });
      const wrapper = await mountSelect();

      const refresh = scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(2);
      expect(dispatchGetListMock).toHaveBeenLastCalledWith(2, PAGE_SIZE);
      expect(getOptions(wrapper)).toHaveLength(60);
      expect(refresh).toHaveBeenCalledTimes(1);
    });

    it('does not fetch when the scroll position is far from the end', async () => {
      const wrapper = await mountSelect();

      scroll(wrapper, 10);
      await flushPromises();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(1);
    });

    it('does not add items that are already loaded', async () => {
      dispatchGetListMock.mockResolvedValueOnce({
        total: 60,
        items: makeGroups(10, 50), // id 50 already exists
      });
      const wrapper = await mountSelect();

      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(getOptions(wrapper)).toHaveLength(59);
    });

    it('stops fetching after a page with fewer items than the page size', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeGroups(10, 51) });
      const wrapper = await mountSelect();
      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();
      expect(dispatchGetListMock).toHaveBeenCalledTimes(2);

      scroll(wrapper, 59);
      await flushPromises();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(2);
    });

    it('notifies when fetching the next page fails', async () => {
      dispatchGetListMock.mockRejectedValueOnce(new Error('network'));
      const wrapper = await mountSelect();

      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(notifyMock).toHaveBeenCalledWith({
        position: 'top',
        type: 'negative',
        message: 'Failed to fetch permission groups',
      });
      expect(getOptions(wrapper)).toHaveLength(PAGE_SIZE);
    });
  });
});
