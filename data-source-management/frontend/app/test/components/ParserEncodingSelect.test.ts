import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { QSelect } from 'quasar';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';

import ParserEncodingSelect from '@/components/ParserEncodingSelect.vue';

interface Encoding {
  codec: string;
  aliases: string[];
  languages: string[];
}

const { storeMock, notifyMock } = vi.hoisted(() => ({
  storeMock: { rows: [] as unknown[], dispatchGetList: vi.fn() },
  notifyMock: vi.fn(),
}));

vi.mock('@/stores/parserEncodingStore', () => ({
  useParserEncodingStore: () => storeMock,
}));

vi.mock('quasar', async (importOriginal) => {
  const actual = await importOriginal<typeof import('quasar')>();
  return {
    ...actual,
    useQuasar: () => ({ notify: notifyMock }),
  };
});

installQuasarPlugin();

const ENCODINGS: Encoding[] = [
  { codec: 'utf-8', aliases: ['u8', 'utf8'], languages: ['all languages'] },
  { codec: 'latin_1', aliases: ['iso-8859-1', 'l1'], languages: ['Western Europe'] },
  { codec: 'cp1251', aliases: ['windows-1251'], languages: ['Bulgarian', 'Russian'] },
];

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
  const wrapper = mount(ParserEncodingSelect, {
    global: { stubs: { QSelect: QSelectStub } },
  });
  await flushPromises();
  return wrapper;
};

const mountSelect = async (
  props: {
    modelValue?: unknown;
    label?: string;
    rules?: Array<(val: unknown) => string | boolean>;
  } = {},
) => {
  const wrapper = mount(ParserEncodingSelect, { props });
  await flushPromises();
  return wrapper;
};

type Wrapper = Awaited<ReturnType<typeof mountSelect>>;

const getSelect = (wrapper: Wrapper) => wrapper.findComponent(QSelect);
const getOptions = (wrapper: Wrapper) => getSelect(wrapper).props('options') as Encoding[];
const getCodecs = (wrapper: Wrapper) => getOptions(wrapper).map((o) => o.codec);

describe('ParserEncodingSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    storeMock.rows = ENCODINGS;
    storeMock.dispatchGetList.mockReset();
    storeMock.dispatchGetList.mockResolvedValue(undefined);
  });

  describe('loading', () => {
    it('fetches the encodings once on mount', async () => {
      await mountSelect();

      expect(storeMock.dispatchGetList).toHaveBeenCalledTimes(1);
      expect(storeMock.dispatchGetList).toHaveBeenCalledWith();
    });

    it('passes the store rows as options to the select', async () => {
      const wrapper = await mountSelect();

      expect(getCodecs(wrapper)).toEqual(['utf-8', 'latin_1', 'cp1251']);
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

      expect(getSelect(wrapper).props('label')).toBe('Select the file encoding *');
    });

    it('uses the label prop when provided', async () => {
      const wrapper = await mountSelect({ label: 'Encoding' });

      expect(getSelect(wrapper).props('label')).toBe('Encoding');
    });

    it('configures the select to use the codec as value and label', async () => {
      const wrapper = await mountSelect();
      const select = getSelect(wrapper);

      expect(select.props('optionValue')).toBe('codec');
      expect(select.props('optionLabel')).toBe('codec');
      expect(select.props('emitValue')).toBe(true);
      expect(select.props('mapOptions')).toBe(true);
    });

    it('passes attrs such as rules through to the select', async () => {
      const rule = (val: unknown) => !!val || 'Encoding is required';

      const wrapper = await mountSelect({ rules: [rule] });

      expect(getSelect(wrapper).props('rules')).toEqual([rule]);
    });

    it('passes the modelValue to the select and updates it on prop change', async () => {
      const wrapper = await mountSelect({ modelValue: 'utf-8' });
      expect(getSelect(wrapper).props('modelValue')).toBe('utf-8');

      await wrapper.setProps({ modelValue: 'latin_1' });

      expect(getSelect(wrapper).props('modelValue')).toBe('latin_1');
    });

    it('emits update:modelValue when the select changes', async () => {
      const wrapper = await mountSelect();

      getSelect(wrapper).vm.$emit('update:modelValue', 'cp1251');

      expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual(['cp1251']);
    });
  });

  describe('filtering', () => {
    const emitFilter = (wrapper: Wrapper, val: string) => {
      const update = vi.fn((cb: () => void) => cb());
      getSelect(wrapper).vm.$emit('filter', val, update);
      return update;
    };

    it.for([
      { case: 'codec', needle: 'latin', expected: ['latin_1'] },
      { case: 'alias', needle: 'windows-1251', expected: ['cp1251'] },
      { case: 'language', needle: 'russian', expected: ['cp1251'] },
      { case: 'codec (case-insensitive)', needle: 'UTF', expected: ['utf-8'] },
      { case: 'alias (case-insensitive)', needle: 'ISO-8859', expected: ['latin_1'] },
      { case: 'language (case-insensitive)', needle: 'WESTERN', expected: ['latin_1'] },
    ])('matches by $case', async ({ needle, expected }) => {
      const wrapper = await mountSelect();

      const update = emitFilter(wrapper, needle);
      await wrapper.vm.$nextTick();

      expect(update).toHaveBeenCalledTimes(1);
      expect(getCodecs(wrapper)).toEqual(expected);
    });

    it('returns every option that matches in any of the fields', async () => {
      const wrapper = await mountSelect();

      // "1" matches latin_1 (codec) and cp1251 (codec + alias), but not utf-8
      emitFilter(wrapper, '1');
      await wrapper.vm.$nextTick();

      expect(getCodecs(wrapper)).toEqual(['latin_1', 'cp1251']);
    });

    it('shows all options again for an empty search term', async () => {
      const wrapper = await mountSelect();
      emitFilter(wrapper, 'latin');
      await wrapper.vm.$nextTick();
      expect(getOptions(wrapper)).toHaveLength(1);

      const update = emitFilter(wrapper, '');
      await wrapper.vm.$nextTick();

      expect(update).toHaveBeenCalledTimes(1);
      expect(getOptions(wrapper)).toHaveLength(3);
    });

    it('shows no options when nothing matches', async () => {
      const wrapper = await mountSelect();

      emitFilter(wrapper, 'does_not_exist');
      await wrapper.vm.$nextTick();

      expect(getOptions(wrapper)).toEqual([]);
    });
  });

  describe('option rendering', () => {
    it('shows codec, aliases and languages of every option', async () => {
      const wrapper = await mountOptionList();

      const options = wrapper.findAll('.option');

      expect(options).toHaveLength(3);
      expect(options[0]!.text()).toContain('utf-8');
      expect(options[0]!.text()).toContain('aliases: u8,utf8');
      expect(options[0]!.text()).toContain('languages: all languages');
      expect(options[2]!.text()).toContain('languages: Bulgarian,Russian');
    });

    it('shows "No results" when there are no options', async () => {
      storeMock.rows = [];

      const wrapper = await mountOptionList();

      expect(wrapper.find('.option').exists()).toBe(false);
      expect(wrapper.text()).toContain('No results');
    });
  });
});
