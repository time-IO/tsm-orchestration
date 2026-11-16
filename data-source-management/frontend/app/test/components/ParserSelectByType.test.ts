import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { QChip, QIcon } from 'quasar';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';

import ParserSelectByType from '@/components/ParserSelectByType.vue'; // adjust path
import type { ParserRead, ParserSelectOption } from '@/services/types';
import { truncateText } from '@/utils/string_utils';

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const { resolveMock } = vi.hoisted(() => ({
  resolveMock: vi.fn((location: { path: string }) => ({ href: `#${location.path}` })),
}));

vi.mock('vue-router', () => ({
  useRouter: () => ({ resolve: resolveMock }),
}));

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

// Renders the control/hint slots; the click listener falls through to the root div.
const BaseFieldStub = defineComponent({
  name: 'BaseField',
  props: ['modelValue', 'disable', 'label'],
  setup:
    (_, { slots }) =>
    () =>
      h('div', { class: 'base-field' }, [slots.control?.(), slots.hint?.()]),
});

// QDialog normally renders in a portal -> render the content inline, only while open.
const QDialogStub = defineComponent({
  name: 'QDialog',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  setup:
    (props, { slots }) =>
    () =>
      props.modelValue ? h('div', { class: 'dialog-stub' }, slots.default?.()) : null,
});

const QTooltipStub = defineComponent({
  name: 'QTooltip',
  setup:
    (_, { slots }) =>
    () =>
      h('div', { class: 'tooltip' }, slots.default?.()),
});

const ParserTypeSelectStub = defineComponent({
  name: 'ParserTypeSelect',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'parser-type-select-stub' }),
});

const ParserSelectStub = defineComponent({
  name: 'ParserSelect',
  props: ['modelValue', 'disable', 'permission_group_id', 'parser_type', 'preselected_item_id'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'parser-select-stub' }),
});

const globalOptions = {
  stubs: {
    BaseField: BaseFieldStub,
    QDialog: QDialogStub,
    QTooltip: QTooltipStub,
    ParserTypeSelect: ParserTypeSelectStub,
    ParserSelect: ParserSelectStub,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeParser = (overrides: Record<string, unknown>) =>
  ({ id: 1, name: 'Parser', ...overrides }) as unknown as ParserSelectOption & ParserRead;

const csvParser = makeParser({
  id: 5,
  name: 'My CSV parser',
  parser_type: 'csv',
  delimiter: ';',
  timestamp_columns: [
    { id: 1, column: 'ts', timestamp_format: '%Y-%m-%d' },
    { id: 2, column: 'time', timestamp_format: '%H:%M' },
  ],
});

const jsonParser = makeParser({
  id: 6,
  name: 'My JSON parser',
  parser_type: 'json',
  timestamp_keys: [{ id: 1, key: 'Datetime', format: '%Y-%m-%dT%H:%M:%S' }],
});

const soilcanParser = makeParser({
  id: 7,
  name: 'My soilcan parser',
  parser_type: 'soilcan',
  type: 'type-a',
  header: true,
});

function mountParserSelectByType(props: Record<string, unknown> = {}) {
  const wrapper = mount(ParserSelectByType, {
    props: {
      modelValue: null,
      ...props,
    },
    global: globalOptions,
  });
  return wrapper;
}

const chipTexts = (wrapper: VueWrapper) => wrapper.findAllComponents(QChip).map((c) => c.text());

const dialogOpen = (wrapper: VueWrapper) => wrapper.find('.dialog-stub').exists();

const openDialog = async (wrapper: VueWrapper) => {
  await wrapper.find('.base-field').trigger('click');
};

const chooseType = async (wrapper: VueWrapper, type: string | null) => {
  wrapper.findComponent(ParserTypeSelectStub).vm.$emit('update:modelValue', type);
  await flushPromises();
};

const pickParser = async (wrapper: VueWrapper, parser: ParserSelectOption | null) => {
  wrapper.findComponent(ParserSelectStub).vm.$emit('update:modelValue', parser);
  await flushPromises();
};

const lastEmitted = (wrapper: VueWrapper) => wrapper.emitted('update:modelValue')?.at(-1);

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ParserSelectByType', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('initialization', () => {
    it('shows no parser details and keeps the dialog closed without a selection', () => {
      const wrapper = mountParserSelectByType();

      expect(wrapper.findAllComponents(QChip)).toHaveLength(0);
      expect(wrapper.findComponent(BaseFieldStub).props('modelValue')).toBeNull();
      expect(dialogOpen(wrapper)).toBe(false);
    });

    it('shows the permission group hint only when disabled', async () => {
      const wrapper = mountParserSelectByType();
      const hint = 'Select a Permission Group first';

      expect(wrapper.text()).not.toContain(hint);

      await wrapper.setProps({ disable: true } as never);

      expect(wrapper.text()).toContain(hint);
      expect(wrapper.findComponent(BaseFieldStub).props('disable')).toBe(true);
    });

    it('takes over a preselected parser and emits its id', () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });

      expect(lastEmitted(wrapper)).toEqual([5]);
      expect(wrapper.findComponent(BaseFieldStub).props('modelValue')).toBe(5);
      expect(chipTexts(wrapper)).toContain('My CSV parser');
    });

    it('truncates long parser names to 50 characters', () => {
      const longName = 'x'.repeat(80);
      const wrapper = mountParserSelectByType({
        preselectedParser: makeParser({ ...csvParser, name: longName }),
      });

      expect(chipTexts(wrapper)[0]).toBe(truncateText(longName, 50));
    });
  });

  describe('parser details', () => {
    it('shows name, type, delimiter and every timestamp column for a csv parser', () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });

      expect(chipTexts(wrapper)).toEqual([
        'My CSV parser',
        'csv',
        ';',
        'ts:%Y-%m-%d',
        'time:%H:%M',
      ]);
      expect(wrapper.text()).toContain('Delimiter:');
      expect(wrapper.text()).toContain('Timestamp Column:');
    });

    it('shows name, type and timestamp keys for a json parser', () => {
      const wrapper = mountParserSelectByType({ preselectedParser: jsonParser });

      expect(chipTexts(wrapper)).toEqual(['My JSON parser', 'json', 'Datetime:%Y-%m-%dT%H:%M:%S']);
      expect(wrapper.text()).toContain('Timestamp Key:');
      expect(wrapper.text()).not.toContain('Delimiter:');
    });

    it('shows soilcan type and header flag for a soilcan parser', async () => {
      const wrapper = mountParserSelectByType({ preselectedParser: soilcanParser });

      expect(chipTexts(wrapper)).toEqual(['My soilcan parser', 'soilcan', 'type-a', 'Yes']);

      await wrapper.setProps({ preselectedParser: { ...soilcanParser, header: false } } as never);

      expect(chipTexts(wrapper).at(-1)).toBe('No');
    });

    it('does not fail when a csv parser has no timestamp columns', () => {
      const wrapper = mountParserSelectByType({
        preselectedParser: makeParser({ ...csvParser, timestamp_columns: undefined }),
      });

      expect(chipTexts(wrapper)).toEqual(['My CSV parser', 'csv', ';']);
    });
  });

  describe('prop changes', () => {
    it('updates selection, details and emitted id when preselectedParser changes', async () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });

      await wrapper.setProps({ preselectedParser: jsonParser } as never);

      expect(lastEmitted(wrapper)).toEqual([6]);
      expect(chipTexts(wrapper)).toContain('My JSON parser');
      expect(chipTexts(wrapper)).not.toContain('My CSV parser');
    });

    it('ignores a null preselectedParser and keeps the current selection', async () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });

      await wrapper.setProps({ preselectedParser: null } as never);

      expect(chipTexts(wrapper)).toContain('My CSV parser');
      expect(lastEmitted(wrapper)).toEqual([5]);
    });

    it('resets the selection when the permission group changes from one group to another', async () => {
      const wrapper = mountParserSelectByType({
        permissionGroupId: 1,
        preselectedParser: csvParser,
      });

      await wrapper.setProps({ permissionGroupId: 2 } as never);

      expect(wrapper.findAllComponents(QChip)).toHaveLength(0);
      expect(lastEmitted(wrapper)).toEqual([null]);
    });

    it.each([
      ['undefined to a group', undefined, 2],
      ['null to a group', null, 2],
    ])(
      'keeps the selection when the permission group changes from %s',
      async (_label, from, to) => {
        const wrapper = mountParserSelectByType({
          permissionGroupId: from,
          preselectedParser: csvParser,
        });

        await wrapper.setProps({ permissionGroupId: to } as never);

        expect(chipTexts(wrapper)).toContain('My CSV parser');
        expect(lastEmitted(wrapper)).toEqual([5]);
      },
    );
  });

  describe('selection dialog', () => {
    it('opens the dialog when the field is clicked', async () => {
      const wrapper = mountParserSelectByType();

      await openDialog(wrapper);

      expect(dialogOpen(wrapper)).toBe(true);
      expect(wrapper.text()).toContain('Select Parser');
    });

    it('shows the parser select only after a type was chosen', async () => {
      const wrapper = mountParserSelectByType();
      await openDialog(wrapper);

      expect(wrapper.findComponent(ParserSelectStub).exists()).toBe(false);

      await chooseType(wrapper, 'csv');

      expect(wrapper.findComponent(ParserSelectStub).exists()).toBe(true);
      expect(wrapper.text()).toContain('2. Choose parser');
    });

    it('hides the parser select again when the type is cleared', async () => {
      const wrapper = mountParserSelectByType();
      await openDialog(wrapper);
      await chooseType(wrapper, 'csv');

      await chooseType(wrapper, null);

      expect(wrapper.findComponent(ParserSelectStub).exists()).toBe(false);
    });

    it('passes type, permission group, preselected id and disable to the parser select', async () => {
      const wrapper = mountParserSelectByType({
        permissionGroupId: 3,
        preselectedParser: csvParser,
      });
      await openDialog(wrapper);

      const select = wrapper.findComponent(ParserSelectStub);

      expect(select.props('parser_type')).toBe('csv');
      expect(select.props('permission_group_id')).toBe(3);
      expect(select.props('preselected_item_id')).toBe(5);
      expect(select.props('disable')).toBeFalsy();
    });

    it('passes null as permission group when none is given', async () => {
      const wrapper = mountParserSelectByType();
      await openDialog(wrapper);
      await chooseType(wrapper, 'json');

      expect(wrapper.findComponent(ParserSelectStub).props('permission_group_id')).toBeNull();
    });

    it('preselects the type of the current selection when reopening', async () => {
      const wrapper = mountParserSelectByType({ preselectedParser: jsonParser });
      await openDialog(wrapper);

      expect(wrapper.findComponent(ParserTypeSelectStub).props('modelValue')).toBe('json');
      expect(wrapper.findComponent(ParserSelectStub).props('modelValue')).toMatchObject({ id: 6 });
    });

    it('clears the draft parser when another type is chosen', async () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });
      await openDialog(wrapper);

      await chooseType(wrapper, 'json');

      expect(wrapper.findComponent(ParserSelectStub).props('modelValue')).toBeNull();
    });
  });

  describe('parser selection (v-model)', () => {
    it('emits the id, shows the details and closes the dialog when a parser is picked', async () => {
      const wrapper = mountParserSelectByType();
      await openDialog(wrapper);
      await chooseType(wrapper, 'soilcan');

      await pickParser(wrapper, soilcanParser);

      expect(lastEmitted(wrapper)).toEqual([7]);
      expect(wrapper.findComponent(BaseFieldStub).props('modelValue')).toBe(7);
      expect(chipTexts(wrapper)).toContain('My soilcan parser');
      expect(dialogOpen(wrapper)).toBe(false);
    });

    it.each([[null], [undefined]])(
      'ignores a %s pick: no emit, dialog stays open, selection unchanged',
      async (value) => {
        const wrapper = mountParserSelectByType();
        await openDialog(wrapper);
        await chooseType(wrapper, 'csv');

        await pickParser(wrapper, value as null);

        expect(wrapper.emitted('update:modelValue')).toBeUndefined();
        expect(dialogOpen(wrapper)).toBe(true);
        expect(wrapper.findAllComponents(QChip)).toHaveLength(0);
      },
    );

    it('replaces the previous selection when another parser is picked', async () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });
      await openDialog(wrapper);
      await chooseType(wrapper, 'json');

      await pickParser(wrapper, jsonParser);

      expect(lastEmitted(wrapper)).toEqual([6]);
      expect(chipTexts(wrapper)).toContain('My JSON parser');
      expect(chipTexts(wrapper)).not.toContain('My CSV parser');
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

    const findLaunchIcon = (wrapper: VueWrapper) =>
      wrapper.findAllComponents(QIcon).find((i) => i.props('name') === 'launch')!;

    it.each([
      ['csv', csvParser, '/parser/csv/5'],
      ['json', jsonParser, '/parser/json/6'],
      ['soilcan', soilcanParser, '/parser/soilcan/7'],
    ])('opens the %s parser in a new window', async (_type, parser, path) => {
      const wrapper = mountParserSelectByType({ preselectedParser: parser });

      await findLaunchIcon(wrapper).trigger('click');

      expect(resolveMock).toHaveBeenCalledWith({ path });
      expect(openSpy).toHaveBeenCalledTimes(1);
      expect(openSpy).toHaveBeenCalledWith(`#${path}`, '_blank');
    });

    it('does not open the selection dialog when the launch icon is clicked', async () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });

      await findLaunchIcon(wrapper).trigger('click');

      expect(dialogOpen(wrapper)).toBe(false);
    });

    it('shows the "Open in new window" tooltip', () => {
      const wrapper = mountParserSelectByType({ preselectedParser: csvParser });

      expect(wrapper.find('.tooltip').text()).toContain('Open in new window');
    });
  });
});
