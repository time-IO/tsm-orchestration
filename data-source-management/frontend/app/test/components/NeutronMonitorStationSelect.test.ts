import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { QSelect } from 'quasar';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';

import NeutronMonitorStationSelect from '@/components/NeutronMonitorStationSelect.vue';
import type { NeutronMonitorStation } from '@/services/neutron_monitor_stations/types';

const { dispatchGetListMock, notifyMock } = vi.hoisted(() => ({
  dispatchGetListMock: vi.fn(),
  notifyMock: vi.fn(),
}));

vi.mock('@/stores/neutronMonitorStationStore', () => ({
  useNeutronMonitorStationStore: () => ({ dispatchGetList: dispatchGetListMock }),
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

// The option slots of a real QSelect only render inside a popup menu.
// This stub renders them inline, so the slot content can be tested.
const QSelectStub = defineComponent({
  name: 'QSelect',
  inheritAttrs: false,
  props: ['options', 'modelValue'],
  setup:
    (props, { slots }) =>
    () =>
      h(
        'div',
        { class: 'q-select-stub' },
        props.options?.length
          ? (props.options as unknown[]).map((opt) =>
              h('div', { class: 'option' }, slots.option?.({ opt, itemProps: {} })),
            )
          : slots['no-option']?.(),
      ),
});

const mountOptionList = async () => {
  const wrapper = mount(NeutronMonitorStationSelect, {
    global: { stubs: { QSelect: QSelectStub } },
  });
  await flushPromises();
  return wrapper;
};

const makeStation = (id: number, stationId: string, description = `Description ${id}`) =>
  ({ id, station_id: stationId, description }) as NeutronMonitorStation;

const makeStations = (count: number, startId = 1): NeutronMonitorStation[] =>
  Array.from({ length: count }, (_, i) => makeStation(startId + i, `STATION-${startId + i}`));

const mountSelect = async (
  props: {
    modelValue?: unknown;
    preselectedItem?: NeutronMonitorStation | null;
  } = {},
) => {
  const wrapper = mount(NeutronMonitorStationSelect, { props });
  await flushPromises();
  return wrapper;
};

type Wrapper = Awaited<ReturnType<typeof mountSelect>>;

const getSelect = (wrapper: Wrapper) => wrapper.findComponent(QSelect);
const getOptions = (wrapper: Wrapper) =>
  getSelect(wrapper).props('options') as NeutronMonitorStation[];
const getIds = (wrapper: Wrapper) => getOptions(wrapper).map((o) => o.id);

describe('NeutronMonitorStationSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dispatchGetListMock.mockReset();
    dispatchGetListMock.mockResolvedValue({ total: 2, items: makeStations(2) });
  });

  describe('loading', () => {
    it('fetches the first page with the page size on mount', async () => {
      await mountSelect();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(1);
      expect(dispatchGetListMock).toHaveBeenCalledWith(1, PAGE_SIZE);
    });

    it('passes the fetched items as options to the select', async () => {
      const wrapper = await mountSelect();

      expect(getIds(wrapper)).toEqual([1, 2]);
    });

    it('notifies and keeps the options empty when fetching fails', async () => {
      dispatchGetListMock.mockRejectedValue(new Error('network'));

      const wrapper = await mountSelect();

      expect(notifyMock).toHaveBeenCalledTimes(1);
      expect(notifyMock).toHaveBeenCalledWith({
        position: 'top',
        type: 'negative',
        message: 'Failed to fetch stations',
      });
      expect(getOptions(wrapper)).toEqual([]);
    });
  });

  describe('props and v-model', () => {
    it('uses the fixed label', async () => {
      const wrapper = await mountSelect();

      expect(getSelect(wrapper).props('label')).toBe('Select a station *');
    });

    it('configures the select to use the id as value and the station_id as label', async () => {
      const wrapper = await mountSelect();
      const select = getSelect(wrapper);

      expect(select.props('optionValue')).toBe('id');
      expect(select.props('optionLabel')).toBe('station_id');
      expect(select.props('emitValue')).toBe(true);
      expect(select.props('mapOptions')).toBe(true);
    });

    it('is clearable', async () => {
      const wrapper = await mountSelect();

      expect(getSelect(wrapper).props('clearable')).toBe(true);
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

    it('emits null when the selection is cleared', async () => {
      const wrapper = await mountSelect({ modelValue: 1 });

      getSelect(wrapper).vm.$emit('update:modelValue', null);

      expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([null]);
    });
  });

  describe('validation', () => {
    it('requires a value via the REQUIRED rule', async () => {
      const wrapper = await mountSelect();
      const rules = getSelect(wrapper).props('rules') as Array<(val: unknown) => string | boolean>;

      expect(rules).toHaveLength(1);
      expect(rules[0]!(null)).not.toBe(true);
      expect(rules[0]!(1)).toBe(true);
    });
  });

  describe('filtering', () => {
    const emitFilter = (wrapper: Wrapper, val: string) => {
      const update = vi.fn((cb: () => void) => cb());
      getSelect(wrapper).vm.$emit('filter', val, update);
      return update;
    };

    beforeEach(() => {
      dispatchGetListMock.mockResolvedValue({
        total: 3,
        items: [
          makeStation(1, 'JUNG', 'Jungfraujoch'),
          makeStation(2, 'KIEL', 'Kiel'),
          makeStation(3, 'KIEL2', 'Second Kiel'),
        ],
      });
    });

    it.for([
      { case: 'prefix', needle: 'KIEL', expected: [2, 3] },
      { case: 'substring in the middle', needle: 'ung', expected: [1] },
      { case: 'case-insensitive', needle: 'jUnG', expected: [1] },
    ])('matches the station_id by $case', async ({ needle, expected }) => {
      const wrapper = await mountSelect();

      const update = emitFilter(wrapper, needle);
      await wrapper.vm.$nextTick();

      expect(update).toHaveBeenCalledTimes(1);
      expect(getIds(wrapper)).toEqual(expected);
    });

    it('does not search the description', async () => {
      const wrapper = await mountSelect();

      emitFilter(wrapper, 'jungfraujoch');
      await wrapper.vm.$nextTick();

      expect(getOptions(wrapper)).toEqual([]);
    });

    it('shows all options again for an empty search term', async () => {
      const wrapper = await mountSelect();
      emitFilter(wrapper, 'jung');
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
      const extra = makeStation(99, 'EXTRA');

      await wrapper.setProps({ preselectedItem: extra });

      expect(getIds(wrapper)).toEqual([1, 2, 99]);
    });

    it('does not add a preselected item that is already in the options', async () => {
      const wrapper = await mountSelect();
      const existing = getOptions(wrapper)[0]!;

      await wrapper.setProps({ preselectedItem: { ...existing } });

      expect(getIds(wrapper)).toEqual([1, 2]);
    });

    it('keeps the options when the preselected item is cleared', async () => {
      const wrapper = await mountSelect();
      await wrapper.setProps({ preselectedItem: makeStation(99, 'EXTRA') });

      await wrapper.setProps({ preselectedItem: null });

      expect(getIds(wrapper)).toEqual([1, 2, 99]);
    });
  });

  describe('pagination via virtual scroll', () => {
    const scroll = (wrapper: Wrapper, to: number, refresh = vi.fn()) => {
      getSelect(wrapper).vm.$emit('virtual-scroll', { to, ref: { refresh } });
      return refresh;
    };

    beforeEach(() => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeStations(PAGE_SIZE, 1) });
    });

    it('fetches the next page near the end of the list and appends the items', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeStations(10, 51) });
      const wrapper = await mountSelect();

      const refresh = scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(2);
      expect(dispatchGetListMock).toHaveBeenLastCalledWith(2, PAGE_SIZE);
      expect(getOptions(wrapper)).toHaveLength(60);
      expect(refresh).toHaveBeenCalledTimes(1);
    });

    it.for([
      { to: 10, expectedCalls: 1 },
      { to: 46, expectedCalls: 1 }, // lastIndex - 3: too far away
      { to: 47, expectedCalls: 2 }, // lastIndex - 2: treshold reached
    ])('fetches only at the threshold (to = $to)', async ({ to, expectedCalls }) => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeStations(10, 51) });
      const wrapper = await mountSelect();

      scroll(wrapper, to);
      await flushPromises();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(expectedCalls);
    });

    it('does not add items that are already loaded', async () => {
      dispatchGetListMock.mockResolvedValueOnce({
        total: 60,
        items: makeStations(10, 50), // id 50 already exists
      });
      const wrapper = await mountSelect();

      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(getOptions(wrapper)).toHaveLength(59);
    });

    it('stops fetching after a page with fewer items than the page size', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeStations(10, 51) });
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
        message: 'Failed to fetch stations',
      });
      expect(getOptions(wrapper)).toHaveLength(PAGE_SIZE);
    });

    it('does not fail when the virtual scroll event has no ref', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeStations(10, 51) });
      const wrapper = await mountSelect();

      getSelect(wrapper).vm.$emit('virtual-scroll', { to: PAGE_SIZE - 1 });
      await flushPromises();

      expect(getOptions(wrapper)).toHaveLength(60);
    });

    it('ignores a scroll while the previous fetch is still running', async () => {
      let finishFetch!: (value: unknown) => void;
      dispatchGetListMock.mockReturnValueOnce(new Promise((resolve) => (finishFetch = resolve)));
      const wrapper = await mountSelect();

      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();
      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(2);
      finishFetch({ total: 60, items: makeStations(10, 51) });
      await flushPromises();
    });

    it('lets only one fetch run when two scrolls arrive at once', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeStations(10, 51) });
      const wrapper = await mountSelect();

      scroll(wrapper, PAGE_SIZE - 1);
      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(dispatchGetListMock).toHaveBeenCalledTimes(2);
      expect(getOptions(wrapper)).toHaveLength(60);
    });
  });


  describe('option rendering', () => {
    it('shows station_id and description of every option', async () => {
      dispatchGetListMock.mockResolvedValue({
        total: 2,
        items: [makeStation(1, 'JUNG', 'Jungfraujoch'), makeStation(2, 'KIEL', 'Kiel')],
      });

      const wrapper = await mountOptionList();
      const options = wrapper.findAll('.option');

      expect(options).toHaveLength(2);
      expect(options[0]!.text()).toContain('JUNG');
      expect(options[0]!.text()).toContain('Jungfraujoch');
      expect(options[1]!.text()).toContain('KIEL');
    });

    it('shows "No results" when there are no options', async () => {
      dispatchGetListMock.mockResolvedValue({ total: 0, items: [] });

      const wrapper = await mountOptionList();

      expect(wrapper.find('.option').exists()).toBe(false);
      expect(wrapper.text()).toContain('No results');
    });
  });

});
