import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { QIcon, QSelect } from 'quasar';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';

import ParserSelect from '@/components/ParserSelect.vue'; // adjust path
import { rules } from '@/utils/validation/rules';
import type { ParserSelectOption } from '@/services/types';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const { stores, notifyMock, resolveMock } = vi.hoisted(() => {
  const createStore = () => ({
    rows: [] as Record<string, unknown>[],
    filters: {} as Record<string, unknown>,
    pagination: { rowsPerPage: 0 },
    dispatchGetList: vi.fn(),
    dispatchGetOne: vi.fn(),
  });
  return {
    stores: { csv: createStore(), json: createStore(), soilcan: createStore() },
    notifyMock: vi.fn(),
    resolveMock: vi.fn((location: { path: string }) => ({ href: `#${location.path}` })),
  };
});

vi.mock('@/stores/parserCsvStore', () => ({ useCsvParserStore: () => stores.csv }));
vi.mock('@/stores/parserJsonStore', () => ({ useJsonParserStore: () => stores.json }));
vi.mock('@/stores/parserSoilcanStore', () => ({ useSoilcanParserStore: () => stores.soilcan }));

vi.mock('vue-router', () => ({
  useRouter: () => ({ resolve: resolveMock }),
}));

vi.mock('quasar', async (importOriginal) => {
  const actual = await importOriginal<typeof import('quasar')>();
  return {
    ...actual,
    useQuasar: () => ({ notify: notifyMock }),
  };
});

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

// The option slot of a real QSelect only renders inside a popup menu.
// This stub renders it inline for every option, so the slot content can be tested.
const QSelectStub = defineComponent({
  name: 'QSelect',
  inheritAttrs: false,
  props: ['options', 'modelValue'],
  emits: ['update:modelValue'],
  setup:
    (props, { slots, emit }) =>
    () =>
      h(
        'div',
        { class: 'q-select-stub' },
        props.options?.length
          ? (props.options as unknown[]).map((opt) =>
              h(
                'div',
                { class: 'option', onClick: () => emit('update:modelValue', opt) },
                slots.option?.({ opt, itemProps: {} }),
              ),
            )
          : slots['no-option']?.(),
      ),
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeParser = (id: number, overrides: Record<string, unknown> = {}) => ({
  id,
  name: `Parser ${id}`,
  ...overrides,
});

const mountParserSelect = async (props: Record<string, unknown> = {}) => {
  const wrapper = mount(ParserSelect, {
    props: { modelValue: null, permission_group_id: 1, parser_type: 'csv', ...props },
  });
  await flushPromises();
  return wrapper;
};

// Same props, but QSelect is replaced by QSelectStub (see above)
const mountOptionList = async (props: Record<string, unknown> = {}) => {
  const wrapper = mount(ParserSelect, {
    props: { modelValue: null, permission_group_id: 1, parser_type: 'csv', ...props },
    global: { stubs: { QSelect: QSelectStub } },
  });
  await flushPromises();
  return wrapper;
};

// Same as mountOptionList, but tooltips render their content inline
const mountOptionListWithTooltips = async (props: Record<string, unknown> = {}) => {
  const wrapper = mount(ParserSelect, {
    props: { modelValue: null, permission_group_id: 1, parser_type: 'csv', ...props },
    global: {
      stubs: {
        QSelect: QSelectStub,
        QTooltip: { template: '<i class="tooltip"><slot/></i>' },
      },
    },
  });
  await flushPromises();
  return wrapper;
};

const getSelect = (w: VueWrapper) => w.findComponent(QSelect);

const optionIds = (w: VueWrapper) =>
  (getSelect(w).props('options') as { id: number }[]).map((o) => o.id);

const emitFilter = async (w: VueWrapper, value: string) => {
  getSelect(w).vm.$emit('filter', value, (cb: () => void) => cb());
  await w.vm.$nextTick();
};

const validate = async (w: VueWrapper) =>
  (getSelect(w).vm as unknown as { validate: () => boolean | Promise<boolean> }).validate();

const chipTexts = (option: { findAll: VueWrapper['findAll'] }) =>
  option.findAll('.q-chip').map((c) => c.text());

// Test data only has the fields the component reads, so it is cast once here
const makeOption = (id: number) =>
  ({ ...makeParser(id), parser_type: 'csv' }) as unknown as ParserSelectOption;
// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ParserSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    for (const store of Object.values(stores)) {
      store.rows = [];
      store.filters = {};
      store.pagination = { rowsPerPage: 0 };
      store.dispatchGetList.mockReset().mockResolvedValue(undefined);
      store.dispatchGetOne.mockReset();
    }
  });

  describe('initialization', () => {
    it('fetches the parser list of the given type for the given permission group', async () => {
      await mountParserSelect({ permission_group_id: 3, parser_type: 'json' });

      expect(stores.json.dispatchGetList).toHaveBeenCalledTimes(1);
      expect(stores.json.filters.permission_group_id).toBe(3);
      expect(stores.json.pagination.rowsPerPage).toBe(250);
      expect(stores.csv.dispatchGetList).not.toHaveBeenCalled();
      expect(stores.soilcan.dispatchGetList).not.toHaveBeenCalled();
    });

    it.each([
      ['no permission group', { permission_group_id: null }],
      ['no parser type', { parser_type: null }],
    ])('does not fetch the list with %s', async (_label, props) => {
      await mountParserSelect(props);

      for (const store of Object.values(stores)) {
        expect(store.dispatchGetList).not.toHaveBeenCalled();
      }
    });

    it('offers the store rows as options, enriched with the parser type', async () => {
      stores.csv.rows = [makeParser(1), makeParser(2)];

      const w = await mountParserSelect();

      expect(getSelect(w).props('options')).toEqual([
        { id: 1, name: 'Parser 1', parser_type: 'csv' },
        { id: 2, name: 'Parser 2', parser_type: 'csv' },
      ]);
    });

    it('offers no options and fetches nothing for an unknown parser type', async () => {
      stores.csv.rows = [makeParser(1)];

      const w = await mountParserSelect({ parser_type: 'xml' });

      expect(getSelect(w).props('options')).toEqual([]);
      for (const store of Object.values(stores)) {
        expect(store.dispatchGetList).not.toHaveBeenCalled();
      }
    });

    it('shows the hint only without a permission group', async () => {
      const hint = 'Select Permission Group first';
      const w = await mountParserSelect({ permission_group_id: null });

      expect(w.text()).toContain(hint);

      await w.setProps({ permission_group_id: 1 });

      expect(w.text()).not.toContain(hint);
    });

    it('passes the label and the REQUIRED rule to the QSelect', async () => {
      const w = await mountParserSelect();

      expect(getSelect(w).props('label')).toBe('Select the parser *');
      expect(getSelect(w).props('rules')).toEqual([rules.REQUIRED]);
    });
  });

  describe('required field', () => {
    it('fails validation without a selected parser and passes with one', async () => {
      const w = await mountParserSelect({ modelValue: null });

      expect(await validate(w)).toBe(false);

      await w.setProps({ modelValue: makeOption(1) });

      expect(await validate(w)).toBe(true);
    });
  });

  describe('prop changes', () => {
    it('refetches with the new permission group when it changes', async () => {
      const w = await mountParserSelect({ permission_group_id: 1 });

      await w.setProps({ permission_group_id: 2 });
      await flushPromises();

      expect(stores.csv.dispatchGetList).toHaveBeenCalledTimes(2);
      expect(stores.csv.filters.permission_group_id).toBe(2);
    });

    it('resets the model when the group changes from one group to another', async () => {
      const w = await mountParserSelect({ permission_group_id: 1, modelValue: makeParser(1) });

      await w.setProps({ permission_group_id: 2 });
      await flushPromises();

      expect(w.emitted('update:modelValue')?.at(-1)).toEqual([null]);
    });

    it('keeps the model when the group changes from null to a group', async () => {
      const w = await mountParserSelect({ permission_group_id: null, modelValue: makeParser(1) });

      await w.setProps({ permission_group_id: 2 });
      await flushPromises();

      expect(w.emitted('update:modelValue')).toBeUndefined();
      expect(stores.csv.dispatchGetList).toHaveBeenCalledTimes(1);
    });

    it('resets the model but does not fetch when the group is cleared', async () => {
      const w = await mountParserSelect({ permission_group_id: 1, modelValue: makeParser(1) });

      await w.setProps({ permission_group_id: null });
      await flushPromises();

      expect(w.emitted('update:modelValue')?.at(-1)).toEqual([null]);
      // only the fetch from mounting
      expect(stores.csv.dispatchGetList).toHaveBeenCalledTimes(1);
    });

    it('fetches from the store of the new type and switches the options', async () => {
      stores.csv.rows = [makeParser(1)];
      stores.json.rows = [makeParser(10), makeParser(11)];
      const w = await mountParserSelect({ parser_type: 'csv' });

      await w.setProps({ parser_type: 'json' });
      await flushPromises();

      expect(stores.json.dispatchGetList).toHaveBeenCalledTimes(1);
      expect(optionIds(w)).toEqual([10, 11]);
    });

    it('does not fetch when the type changes without a permission group', async () => {
      const w = await mountParserSelect({ permission_group_id: null, parser_type: 'csv' });

      await w.setProps({ parser_type: 'json' });
      await flushPromises();

      expect(stores.json.dispatchGetList).not.toHaveBeenCalled();
    });

    it('fetches the missing item when preselected_item_id changes', async () => {
      stores.csv.rows = [makeParser(1)];
      stores.csv.dispatchGetOne.mockResolvedValue(makeParser(99));
      const w = await mountParserSelect();

      await w.setProps({ preselected_item_id: 99 });
      await flushPromises();

      expect(stores.csv.dispatchGetOne).toHaveBeenCalledWith(99);
      expect(optionIds(w)).toEqual([1, 99]);
    });

    it('does not fetch again when preselected_item_id is set to null', async () => {
      stores.csv.dispatchGetOne.mockResolvedValue(makeParser(99));
      const w = await mountParserSelect({ preselected_item_id: 99 });
      expect(stores.csv.dispatchGetOne).toHaveBeenCalledTimes(1);

      await w.setProps({ preselected_item_id: null });
      await flushPromises();

      expect(stores.csv.dispatchGetOne).toHaveBeenCalledTimes(1);
    });

    it('ignores a second fetch while the first one is still running', async () => {
      let finishFetch!: () => void;
      stores.csv.dispatchGetList.mockReturnValue(
        new Promise<void>((resolve) => {
          finishFetch = resolve;
        }),
      );
      const w = await mountParserSelect({ permission_group_id: 1 });

      await w.setProps({ permission_group_id: 2 });
      await flushPromises();

      expect(stores.csv.dispatchGetList).toHaveBeenCalledTimes(1);
      finishFetch();
      await flushPromises();
    });
  });

  describe('preselected item', () => {
    it('fetches the item and appends it when it is not in the list', async () => {
      stores.csv.rows = [makeParser(1), makeParser(2)];
      stores.csv.dispatchGetOne.mockResolvedValue(makeParser(99, { name: 'Missing parser' }));

      const w = await mountParserSelect({ preselected_item_id: 99 });

      expect(stores.csv.dispatchGetOne).toHaveBeenCalledTimes(1);
      expect(stores.csv.dispatchGetOne).toHaveBeenCalledWith(99);
      expect(optionIds(w)).toEqual([1, 2, 99]);
      expect(getSelect(w).props('options')).toContainEqual({
        id: 99,
        name: 'Missing parser',
        parser_type: 'csv',
      });
    });

    it('does not fetch the item when it is already in the list', async () => {
      stores.csv.rows = [makeParser(1), makeParser(2)];

      const w = await mountParserSelect({ preselected_item_id: 2 });

      expect(stores.csv.dispatchGetOne).not.toHaveBeenCalled();
      expect(optionIds(w)).toEqual([1, 2]);
    });

    it('does not fetch the item without a parser type', async () => {
      await mountParserSelect({ parser_type: null, preselected_item_id: 5 });

      for (const store of Object.values(stores)) {
        expect(store.dispatchGetOne).not.toHaveBeenCalled();
      }
    });

    it('offers no options and fetches no item for an unknown parser type', async () => {
      const w = await mountParserSelect({ parser_type: 'xml', preselected_item_id: 5 });

      for (const store of Object.values(stores)) {
        expect(store.dispatchGetOne).not.toHaveBeenCalled();
      }
      expect(optionIds(w)).toEqual([]);
    });
  });

  describe('error states', () => {
    it('notifies and offers no options when fetching the list fails', async () => {
      stores.csv.dispatchGetList.mockRejectedValue(new Error('boom'));

      const w = await mountParserSelect();

      expect(notifyMock).toHaveBeenCalledTimes(1);
      expect(notifyMock).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'negative', message: 'Failed to fetch parsers' }),
      );
      expect(getSelect(w).props('options')).toEqual([]);
    });

    it('notifies but keeps the list when fetching the preselected item fails', async () => {
      stores.csv.rows = [makeParser(1), makeParser(2)];
      stores.csv.dispatchGetOne.mockRejectedValue(new Error('boom'));

      const w = await mountParserSelect({ preselected_item_id: 99 });

      expect(notifyMock).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'negative', message: 'Failed to fetch single parser' }),
      );
      expect(optionIds(w)).toEqual([1, 2]);
    });

    it('can fetch again after a failed fetch', async () => {
      stores.csv.rows = [makeParser(1)];
      stores.csv.dispatchGetList.mockRejectedValueOnce(new Error('boom'));
      const w = await mountParserSelect({ permission_group_id: 1 });
      expect(optionIds(w)).toEqual([]);

      await w.setProps({ permission_group_id: 2 });
      await flushPromises();

      expect(stores.csv.dispatchGetList).toHaveBeenCalledTimes(2);
      expect(optionIds(w)).toEqual([1]);
    });
  });

  describe('filtering', () => {
    const rows = [
      makeParser(1, { name: 'Alpha CSV' }),
      makeParser(2, { name: 'Beta CSV' }),
      makeParser(3, { name: 'alphabet' }),
    ];

    it('filters the options by name, case-insensitively', async () => {
      stores.csv.rows = rows;
      const w = await mountParserSelect();

      await emitFilter(w, 'ALPH');

      expect(optionIds(w)).toEqual([1, 3]);
    });

    it('offers no options when nothing matches', async () => {
      stores.csv.rows = rows;
      const w = await mountParserSelect();

      await emitFilter(w, 'zzz');

      expect(optionIds(w)).toEqual([]);
    });

    it('restores the full list when the filter is cleared', async () => {
      stores.csv.rows = rows;
      const w = await mountParserSelect();
      await emitFilter(w, 'beta');
      expect(optionIds(w)).toEqual([2]);

      await emitFilter(w, '');

      expect(optionIds(w)).toEqual([1, 2, 3]);
    });
  });

  describe('v-model', () => {
    it('passes the model value to the QSelect', async () => {
      const parser = makeParser(1);

      const w = await mountParserSelect({ modelValue: parser });

      expect(getSelect(w).props('modelValue')).toEqual(parser);
    });

    it('emits the selected parser object', async () => {
      const parser = { ...makeParser(2), parser_type: 'csv' };
      const w = await mountParserSelect();

      getSelect(w).vm.$emit('update:modelValue', parser);
      await flushPromises();

      expect(w.emitted('update:modelValue')).toEqual([[parser]]);
    });

    it('emits null when the selection is cleared', async () => {
      const w = await mountParserSelect({ modelValue: makeParser(1) });

      getSelect(w).vm.$emit('update:modelValue', null);
      await flushPromises();

      expect(w.emitted('update:modelValue')?.at(-1)).toEqual([null]);
    });
  });

  describe('option rendering', () => {
    it('shows name and parser type of every option', async () => {
      stores.csv.rows = [makeParser(1, { name: 'First' }), makeParser(2, { name: 'Second' })];

      const w = await mountOptionList();
      const options = w.findAll('.option');

      expect(options).toHaveLength(2);
      expect(options[0]!.text()).toContain('First');
      expect(options[1]!.text()).toContain('Second');
      expect(chipTexts(options[0]!)[0]).toBe('csv');
    });

    it('shows delimiter and timestamp columns for a csv parser', async () => {
      stores.csv.rows = [
        makeParser(1, {
          delimiter: ';',
          timestamp_columns: [{ id: 1, column: 'ts', timestamp_format: '%Y-%m-%d' }],
        }),
      ];

      const w = await mountOptionList();

      expect(chipTexts(w.find('.option'))).toEqual(['csv', ';', 'ts:%Y-%m-%d']);
    });

    it('shows timestamp keys for a json parser', async () => {
      stores.json.rows = [
        makeParser(1, {
          timestamp_keys: [{ id: 1, key: 'Datetime', format: '%Y-%m-%dT%H:%M:%S' }],
        }),
      ];

      const w = await mountOptionList({ parser_type: 'json' });

      expect(chipTexts(w.find('.option'))).toEqual(['json', 'Datetime:%Y-%m-%dT%H:%M:%S']);
    });

    it('shows type and header flag for soilcan parsers', async () => {
      stores.soilcan.rows = [
        makeParser(1, { type: 'type-a', header: true }),
        makeParser(2, { type: 'type-b', header: false }),
      ];

      const w = await mountOptionList({ parser_type: 'soilcan' });
      const options = w.findAll('.option');

      expect(chipTexts(options[0]!)).toEqual(['soilcan', 'type-a', 'has header']);
      expect(chipTexts(options[1]!)).toEqual(['soilcan', 'type-b', 'no header']);
    });

    it('shows "No results" when there are no options', async () => {
      const w = await mountOptionList();

      expect(w.text()).toContain('No results');
    });

    it('renders a json parser without timestamp keys', async () => {
      stores.json.rows = [makeParser(1)];

      const w = await mountOptionList({ parser_type: 'json' });

      expect(chipTexts(w.find('.option'))).toEqual(['json']);
    });
  });

  describe('browser effects', () => {
    let openSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
      openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    });

    afterEach(() => {
      openSpy.mockRestore();
    });

    it.each([
      ['csv', '/parser/csv/5'],
      ['json', '/parser/json/5'],
      ['soilcan', '/parser/soilcan/5'],
    ])('opens a %s parser in a new window', async (type, path) => {
      stores[type as keyof typeof stores].rows = [makeParser(5)];
      const w = await mountOptionList({ parser_type: type });

      await w.findComponent(QIcon).trigger('click');

      expect(resolveMock).toHaveBeenCalledWith({ path });
      expect(openSpy).toHaveBeenCalledTimes(1);
      expect(openSpy).toHaveBeenCalledWith(`#${path}`, '_blank');
    });

    it('does not select the option when the launch icon is clicked', async () => {
      stores.csv.rows = [makeParser(5)];
      const w = await mountOptionList();

      await w.findComponent(QIcon).trigger('click');
      expect(w.emitted('update:modelValue')).toBeUndefined();

      // control: clicking the option itself does select it
      await w.find('.option').trigger('click');
      expect(w.emitted('update:modelValue')).toHaveLength(1);
    });

    it.for([
      {
        type: 'csv',
        row: {
          delimiter: ';',
          timestamp_columns: [{ id: 1, column: 'ts', timestamp_format: '%Y' }],
        },
        tooltips: ['Open in new window', 'delimiter', 'timestamp columns'],
      },
      {
        type: 'json',
        row: { timestamp_keys: [{ id: 1, key: 'Datetime', format: '%Y' }] },
        tooltips: ['Open in new window', 'timestamp keys'],
      },
      {
        type: 'soilcan',
        row: { type: 'type-a', header: true },
        tooltips: ['Open in new window', 'type', 'header'],
      },
    ])('renders the tooltips of a $type parser', async (testCase) => {
      stores[testCase.type as keyof typeof stores].rows = [makeParser(1, testCase.row)];

      const w = await mountOptionListWithTooltips({ parser_type: testCase.type });

      expect(w.findAll('.tooltip').map((t) => t.text())).toEqual(testCase.tooltips);
    });
  });
});
