import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { QSelect } from 'quasar';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import MqttParserSelect from '@/components/MqttParserSelect.vue';
import type { MqttParser } from '@/services/parser_mqtt/types';
import { rules } from '@/utils/validation/rules';

const { dispatchGetListMock, dispatchGetOneMock, notifyMock } = vi.hoisted(() => ({
  dispatchGetListMock: vi.fn(),
  dispatchGetOneMock: vi.fn(),
  notifyMock: vi.fn(),
}));

vi.mock('@/stores/parserMqttStore', () => ({
  useMqttParserStore: () => ({
    dispatchGetList: dispatchGetListMock,
    dispatchGetOne: dispatchGetOneMock,
  }),
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

const makeParser = (id: number, name = `Parser ${id}`) => ({ id, name }) as MqttParser;

const makeParsers = (count: number, startId = 1): MqttParser[] =>
  Array.from({ length: count }, (_, i) => makeParser(startId + i));

const mountSelect = async (
  props: {
    modelValue?: unknown;
    preselectedItemId?: number | null;
  } = {},
) => {
  const wrapper = mount(MqttParserSelect, { props });
  await flushPromises();
  return wrapper;
};

type Wrapper = Awaited<ReturnType<typeof mountSelect>>;

const getSelect = (wrapper: Wrapper) => wrapper.findComponent(QSelect);
const getOptions = (wrapper: Wrapper) => getSelect(wrapper).props('options') as MqttParser[];
const getIds = (wrapper: Wrapper) => getOptions(wrapper).map((o) => o.id);

describe('MqttParserSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dispatchGetListMock.mockReset();
    dispatchGetOneMock.mockReset();
    dispatchGetListMock.mockResolvedValue({ total: 2, items: makeParsers(2) });
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
        message: 'Failed to fetch parser',
      });
      expect(getOptions(wrapper)).toEqual([]);
    });
  });

  describe('props and v-model', () => {
    it('uses the fixed label', async () => {
      const wrapper = await mountSelect();

      expect(getSelect(wrapper).props('label')).toBe('Select the parser *');
    });

    it('configures the select to use the id as value and the name as label', async () => {
      const wrapper = await mountSelect();
      const select = getSelect(wrapper);

      expect(select.props('optionValue')).toBe('id');
      expect(select.props('optionLabel')).toBe('name');
      expect(select.props('emitValue')).toBe(true);
      expect(select.props('mapOptions')).toBe(true);
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

  describe('validation', () => {
    it('requires a value via the REQUIRED rule', async () => {
      const wrapper = await mountSelect();

      expect(getSelect(wrapper).props('rules')).toEqual([rules.REQUIRED]);
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
        items: [makeParser(1, 'Campbell Logger'), makeParser(2, 'Zentra ZL6'), makeParser(3, 'campbell-2')],
      });
    });

    it.for([
      { case: 'prefix', needle: 'Zentra', expected: [2] },
      { case: 'substring in the middle', needle: 'logger', expected: [1] },
      { case: 'case-insensitive', needle: 'CAMPBELL', expected: [1, 3] },
    ])('matches the name by $case', async ({ needle, expected }) => {
      const wrapper = await mountSelect();

      const update = emitFilter(wrapper, needle);
      await wrapper.vm.$nextTick();

      expect(update).toHaveBeenCalledTimes(1);
      expect(getIds(wrapper)).toEqual(expected);
    });

    it('shows all options again for an empty search term', async () => {
      const wrapper = await mountSelect();
      emitFilter(wrapper, 'zentra');
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

  describe('preselectedItemId', () => {
    it('fetches a missing preselected parser by id and adds it to the options', async () => {
      dispatchGetOneMock.mockResolvedValue(makeParser(99));
      const wrapper = await mountSelect();

      await wrapper.setProps({ preselectedItemId: 99 });
      await flushPromises();

      expect(dispatchGetOneMock).toHaveBeenCalledTimes(1);
      expect(dispatchGetOneMock).toHaveBeenCalledWith(99);
      expect(getIds(wrapper)).toEqual([1, 2, 99]);
    });

    it('does not fetch a preselected parser that is already in the options', async () => {
      const wrapper = await mountSelect();

      await wrapper.setProps({ preselectedItemId: 1 });
      await flushPromises();

      expect(dispatchGetOneMock).not.toHaveBeenCalled();
      expect(getIds(wrapper)).toEqual([1, 2]);
    });

    it('does nothing when the preselected id is reset to null', async () => {
      const wrapper = await mountSelect({ preselectedItemId: 1 });

      await wrapper.setProps({ preselectedItemId: null });
      await flushPromises();

      expect(dispatchGetOneMock).not.toHaveBeenCalled();
    });
  });

  describe('pagination via virtual scroll', () => {
    const scroll = (wrapper: Wrapper, to: number, refresh = vi.fn()) => {
      getSelect(wrapper).vm.$emit('virtual-scroll', { to, ref: { refresh } });
      return refresh;
    };

    beforeEach(() => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeParsers(PAGE_SIZE, 1) });
    });

    it('fetches the next page near the end of the list and appends the items', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeParsers(10, 51) });
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
        items: makeParsers(10, 50), // id 50 already exists
      });
      const wrapper = await mountSelect();

      scroll(wrapper, PAGE_SIZE - 1);
      await flushPromises();

      expect(getOptions(wrapper)).toHaveLength(59);
    });

    it('stops fetching after a page with fewer items than the page size', async () => {
      dispatchGetListMock.mockResolvedValueOnce({ total: 60, items: makeParsers(10, 51) });
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
        message: 'Failed to fetch parser',
      });
      expect(getOptions(wrapper)).toHaveLength(PAGE_SIZE);
    });
  });
});
