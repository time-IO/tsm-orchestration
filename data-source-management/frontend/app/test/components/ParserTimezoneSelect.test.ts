import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { QSelect } from 'quasar';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ParserTimezoneSelect from '@/components/ParserTimezoneSelect.vue';

const { storeMock, notifyMock } = vi.hoisted(() => ({
  storeMock: { rows: [] as string[], dispatchGetList: vi.fn() },
  notifyMock: vi.fn(),
}));

vi.mock('@/stores/parserTimezoneStore', () => ({
  useParserTimezoneStore: () => storeMock,
}));

vi.mock('quasar', async (importOriginal) => {
  const actual = await importOriginal<typeof import('quasar')>();
  return {
    ...actual,
    useQuasar: () => ({ notify: notifyMock }),
  };
});

installQuasarPlugin();

const TIMEZONES = ['Europe/Berlin', 'Europe/London', 'America/New_York', 'UTC'];

const mountSelect = async (
  props: {
    modelValue?: unknown;
    label?: string;
    rules?: Array<(val: unknown) => string | boolean>;
  } = {},
) => {
  const wrapper = mount(ParserTimezoneSelect, { props });
  await flushPromises();
  return wrapper;
};

type Wrapper = Awaited<ReturnType<typeof mountSelect>>;

const getSelect = (wrapper: Wrapper) => wrapper.findComponent(QSelect);
const getOptions = (wrapper: Wrapper) => getSelect(wrapper).props('options') as string[];

describe('ParserTimezoneSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    storeMock.rows = TIMEZONES;
    storeMock.dispatchGetList.mockReset();
    storeMock.dispatchGetList.mockResolvedValue(undefined);
  });

  describe('loading', () => {
    it('fetches the timezones once on mount', async () => {
      await mountSelect();

      expect(storeMock.dispatchGetList).toHaveBeenCalledTimes(1);
      expect(storeMock.dispatchGetList).toHaveBeenCalledWith();
    });

    it('passes the store rows as options to the select', async () => {
      const wrapper = await mountSelect();

      expect(getOptions(wrapper)).toEqual(TIMEZONES);
    });

    it('notifies when fetching fails', async () => {
      storeMock.dispatchGetList.mockRejectedValue(new Error('network'));

      await mountSelect();

      expect(notifyMock).toHaveBeenCalledTimes(1);
      expect(notifyMock).toHaveBeenCalledWith({
        position: 'top',
        type: 'negative',
        message: 'Failed to fetch stations',
      });
    });
  });

  describe('props and v-model', () => {
    it('uses the default label without a label prop', async () => {
      const wrapper = await mountSelect();

      expect(getSelect(wrapper).props('label')).toBe('Select the timezone *');
    });

    it('uses the label prop when provided', async () => {
      const wrapper = await mountSelect({ label: 'Timezone' });

      expect(getSelect(wrapper).props('label')).toBe('Timezone');
    });

    it('passes attrs such as rules through to the select', async () => {
      const rule = (val: unknown) => !!val || 'Timezone is required';

      const wrapper = await mountSelect({ rules: [rule] });

      expect(getSelect(wrapper).props('rules')).toEqual([rule]);
    });

    it('passes the modelValue to the select and updates it on prop change', async () => {
      const wrapper = await mountSelect({ modelValue: 'UTC' });
      expect(getSelect(wrapper).props('modelValue')).toBe('UTC');

      await wrapper.setProps({ modelValue: 'Europe/Berlin' });

      expect(getSelect(wrapper).props('modelValue')).toBe('Europe/Berlin');
    });

    it('emits update:modelValue when the select changes', async () => {
      const wrapper = await mountSelect();

      getSelect(wrapper).vm.$emit('update:modelValue', 'Europe/London');

      expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual(['Europe/London']);
    });
  });

  describe('filtering', () => {
    const emitFilter = (wrapper: Wrapper, val: string) => {
      const update = vi.fn((cb: () => void) => cb());
      getSelect(wrapper).vm.$emit('filter', val, update);
      return update;
    };

    it.for([
      { case: 'prefix', needle: 'Europe', expected: ['Europe/Berlin', 'Europe/London'] },
      { case: 'substring in the middle', needle: 'york', expected: ['America/New_York'] },
      { case: 'case-insensitive', needle: 'BERLIN', expected: ['Europe/Berlin'] },
      { case: 'exact value', needle: 'utc', expected: ['UTC'] },
    ])('matches by $case', async ({ needle, expected }) => {
      const wrapper = await mountSelect();

      const update = emitFilter(wrapper, needle);
      await wrapper.vm.$nextTick();

      expect(update).toHaveBeenCalledTimes(1);
      expect(getOptions(wrapper)).toEqual(expected);
    });

    it('shows all options again for an empty search term', async () => {
      const wrapper = await mountSelect();
      emitFilter(wrapper, 'berlin');
      await wrapper.vm.$nextTick();
      expect(getOptions(wrapper)).toHaveLength(1);

      const update = emitFilter(wrapper, '');
      await wrapper.vm.$nextTick();

      expect(update).toHaveBeenCalledTimes(1);
      expect(getOptions(wrapper)).toEqual(TIMEZONES);
    });

    it('shows no options when nothing matches', async () => {
      const wrapper = await mountSelect();

      emitFilter(wrapper, 'does_not_exist');
      await wrapper.vm.$nextTick();

      expect(getOptions(wrapper)).toEqual([]);
    });
  });
});
