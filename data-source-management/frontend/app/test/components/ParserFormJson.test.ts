import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, reactive } from 'vue';

import ParserFormJson from '@/components/ParserFormJson.vue'; // adjust path
import type { JsonParserCreate, JsonParserUpdate } from '@/services/parser_json/types'; // adjust path
import { rules } from '@/utils/validation/rules';
import {
  findBtn,
  findBtnsByIcon,
  findInput,
  findInputs,
  getBtn,
  nativeValue,
  QPageStub,
  submit,
  typeInto,
} from './utils/TestUtilsParser';

// Same shape as the local type in ParserFormJson.vue
type JsonParserFormData = JsonParserUpdate & {
  permission_group_id?: number | null;
  timestamp_keys: JsonParserCreate['timestamp_keys'];
};

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

// QTooltip normally renders in a portal on hover only
const QTooltipStub = defineComponent({
  name: 'QTooltip',
  setup:
    (_, { slots }) =>
    () =>
      h('div', { class: 'tooltip' }, slots.default?.()),
});

const PermissionGroupSelectStub = defineComponent({
  name: 'PermissionGroupSelect',
  props: ['modelValue', 'disable', 'rules'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'permission-group-select-stub' }),
});

const ParserTimezoneSelectStub = defineComponent({
  name: 'ParserTimezoneSelect',
  props: ['modelValue', 'rules'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'timezone-select-stub' }),
});

const ParserValidateJsonStub = defineComponent({
  name: 'ParserValidateJson',
  props: ['modelValue', 'formData'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'parser-validate-json-stub' }),
});

const globalOptions = {
  stubs: {
    QPage: QPageStub,
    QTooltip: QTooltipStub,
    PermissionGroupSelect: PermissionGroupSelectStub,
    ParserTimezoneSelect: ParserTimezoneSelectStub,
    ParserValidateJson: ParserValidateJsonStub,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S';
const PANDAS_DOCS_URL = 'https://pandas.pydata.org/docs/reference/api/pandas.Period.strftime.html';

const makeFormData = (overrides: Partial<JsonParserFormData> = {}): JsonParserFormData => ({
  permission_group_id: 1,
  name: 'My parser',
  description: null,
  comment: null,
  measurement_key: null,
  excluded_keys: [],
  timestamp_keys: [{ key: 'Datetime', format: TIMESTAMP_FORMAT }],
  timezone: 'UTC',
  ...overrides,
});

type MountOptions = {
  model?: Partial<JsonParserFormData>;
  props?: Record<string, unknown>;
};

// The model is reactive so that the component's v-model mutations (formData.value.x = ...)
// are visible in the test and also trigger a re-render.
function mountForm({ model, props }: MountOptions = {}) {
  const formData = reactive(makeFormData(model)) as JsonParserFormData;
  const wrapper = mount(ParserFormJson, {
    props: {
      title: 'New JSON Parser',
      isLoading: false,
      backRoute: '/parser/new',
      modelValue: formData,
      ...props,
    },
    global: globalOptions,
  });
  return { wrapper, formData };
}

const validatedData = (wrapper: VueWrapper) =>
  wrapper.findComponent(ParserValidateJsonStub).props('formData') as JsonParserFormData;

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ParserFormJson', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('initialization and props', () => {
    it('renders the title and passes backRoute to the back button', () => {
      const { wrapper } = mountForm({
        props: { title: 'Edit JSON Parser', backRoute: '/parser/json/5' },
      });

      expect(wrapper.find('h5').text()).toBe('Edit JSON Parser');
      expect(getBtn(wrapper, 'back').props('to')).toBe('/parser/json/5');
    });

    it('updates title and back route when the props change', async () => {
      const { wrapper } = mountForm();

      await wrapper.setProps({ title: 'Other title', backRoute: '/somewhere' } as Record<
        string,
        unknown
      >);

      expect(wrapper.find('h5').text()).toBe('Other title');
      expect(getBtn(wrapper, 'back').props('to')).toBe('/somewhere');
    });

    it('shows the experimental notice', () => {
      const { wrapper } = mountForm();

      expect(wrapper.text()).toContain('This feature is experimental');
    });

    it('shows the initial model values in the inputs and selects', () => {
      const { wrapper } = mountForm({
        model: {
          name: 'Parser A',
          description: 'Some description',
          comment: '//',
          measurement_key: 'object',
          permission_group_id: 7,
          timezone: 'Europe/Berlin',
        },
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('Parser A');
      expect(nativeValue(findInput(wrapper, 'Description'))).toBe('Some description');
      expect(nativeValue(findInput(wrapper, 'Comment character'))).toBe('//');
      expect(nativeValue(findInput(wrapper, 'Measurement key'))).toBe('object');
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(7);
      expect(wrapper.findComponent(ParserTimezoneSelectStub).props('modelValue')).toBe(
        'Europe/Berlin',
      );
    });

    it('renders one block per timestamp key and one input per excluded key', () => {
      const { wrapper } = mountForm({
        model: {
          timestamp_keys: [
            { key: 'Date', format: '%Y' },
            { key: 'Time', format: '%H' },
          ],
          excluded_keys: ['a', 'b', 'c'],
        },
      });

      expect(wrapper.text()).toContain('Timestamp Key 1');
      expect(wrapper.text()).toContain('Timestamp Key 2');
      expect(wrapper.text()).not.toContain('Timestamp Key 3');
      expect(findInputs(wrapper, 'Key (e.g.').map(nativeValue)).toEqual(['Date', 'Time']);
      expect(findInputs(wrapper, 'Format (e.g.').map(nativeValue)).toEqual(['%Y', '%H']);
      expect(findInputs(wrapper, 'Excluded key').map(nativeValue)).toEqual(['a', 'b', 'c']);
    });

    it('falls back to an empty default model when no v-model is passed', () => {
      const wrapper = mount(ParserFormJson, {
        props: { title: 'New', isLoading: false, backRoute: '/back' },
        global: globalOptions,
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('');
      expect(wrapper.text()).toContain('At least one timestamp key is required');
      expect(getBtn(wrapper, 'Save').props('disable')).toBe(true);
    });

    it('passes disablePermissionGroup (default false) to the permission group select', async () => {
      const { wrapper } = mountForm();
      const select = () => wrapper.findComponent(PermissionGroupSelectStub);

      expect(select().props('disable')).toBe(false);

      await wrapper.setProps({ disablePermissionGroup: true } as Record<string, unknown>);

      expect(select().props('disable')).toBe(true);
    });
  });

  describe('permission group', () => {
    it('falls back to the permissionGroupId prop when the model has no group', () => {
      const { wrapper } = mountForm({
        model: { permission_group_id: null },
        props: { permissionGroupId: 9 },
      });

      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(9);
    });

    it('prefers the model value over the permissionGroupId prop', () => {
      const { wrapper } = mountForm({
        model: { permission_group_id: 3 },
        props: { permissionGroupId: 9 },
      });

      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(3);
    });

    it('writes the selected group back to the model', () => {
      const { wrapper, formData } = mountForm();

      wrapper.findComponent(PermissionGroupSelectStub).vm.$emit('update:modelValue', 5);

      expect(formData.permission_group_id).toBe(5);
    });

    it('ignores group changes when disablePermissionGroup is true', () => {
      const { wrapper, formData } = mountForm({
        model: { permission_group_id: null },
        props: { disablePermissionGroup: true, permissionGroupId: 9 },
      });

      wrapper.findComponent(PermissionGroupSelectStub).vm.$emit('update:modelValue', 5);

      expect(formData.permission_group_id).toBeNull();
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(9);
    });
  });

  describe('v-model', () => {
    it('writes name, description, comment and measurement key back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Name'), 'New name');
      await typeInto(findInput(wrapper, 'Description'), 'New description');
      await typeInto(findInput(wrapper, 'Comment character'), '//');
      await typeInto(findInput(wrapper, 'Measurement key'), 'object');

      expect(formData.name).toBe('New name');
      expect(formData.description).toBe('New description');
      expect(formData.comment).toBe('//');
      expect(formData.measurement_key).toBe('object');
    });

    it('writes the timezone from the select back to the model', () => {
      const { wrapper, formData } = mountForm();

      wrapper
        .findComponent(ParserTimezoneSelectStub)
        .vm.$emit('update:modelValue', 'Europe/Berlin');

      expect(formData.timezone).toBe('Europe/Berlin');
    });
  });

  describe('timestamp keys', () => {
    it('adds an empty timestamp key', async () => {
      const { wrapper, formData } = mountForm();

      await getBtn(wrapper, 'Add timestamp key').trigger('click');

      expect(formData.timestamp_keys).toEqual([
        { key: 'Datetime', format: TIMESTAMP_FORMAT },
        { key: null, format: null },
      ]);
      expect(wrapper.text()).toContain('Timestamp Key 2');
    });

    it('removes exactly the clicked timestamp key', async () => {
      const { wrapper, formData } = mountForm({
        model: {
          timestamp_keys: [
            { key: 'a', format: '%Y' },
            { key: 'b', format: '%m' },
            { key: 'c', format: '%d' },
          ],
        },
      });

      await findBtnsByIcon(wrapper, 'remove_circle')[1]!.trigger('click');

      expect(formData.timestamp_keys).toEqual([
        { key: 'a', format: '%Y' },
        { key: 'c', format: '%d' },
      ]);
      expect(wrapper.text()).not.toContain('Timestamp Key 3');
    });

    it('writes key and format back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Key (e.g.'), 'ts');
      await typeInto(findInput(wrapper, 'Format (e.g.'), '%d.%m.%Y');

      expect(formData.timestamp_keys[0]).toEqual({ key: 'ts', format: '%d.%m.%Y' });
    });

    it('shows the hint only while no timestamp key exists', async () => {
      const { wrapper } = mountForm({ model: { timestamp_keys: [] } });
      const hint = 'At least one timestamp key is required';

      expect(wrapper.text()).toContain(hint);

      await getBtn(wrapper, 'Add timestamp key').trigger('click');

      expect(wrapper.text()).not.toContain(hint);
    });
  });

  describe('excluded keys', () => {
    it('adds an empty excluded key to an existing list', async () => {
      const { wrapper, formData } = mountForm({ model: { excluded_keys: ['a'] } });

      await getBtn(wrapper, 'Add excluded key').trigger('click');

      expect(formData.excluded_keys).toEqual(['a', '']);
      expect(findInputs(wrapper, 'Excluded key')).toHaveLength(2);
    });

    it('creates the list first when excluded_keys is null', async () => {
      const { wrapper, formData } = mountForm({ model: { excluded_keys: null } });

      expect(findInputs(wrapper, 'Excluded key')).toHaveLength(0);

      await getBtn(wrapper, 'Add excluded key').trigger('click');

      expect(formData.excluded_keys).toEqual(['']);
      expect(findInputs(wrapper, 'Excluded key')).toHaveLength(1);
    });

    it('writes an excluded key back to the model', async () => {
      const { wrapper, formData } = mountForm({ model: { excluded_keys: ['a', 'b'] } });

      await typeInto(findInputs(wrapper, 'Excluded key')[1]!, 'changed');

      expect(formData.excluded_keys).toEqual(['a', 'changed']);
    });

    it('removes exactly the clicked excluded key', async () => {
      // no timestamp keys, so only the excluded key buttons carry the "remove_circle" icon
      const { wrapper, formData } = mountForm({
        model: { timestamp_keys: [], excluded_keys: ['a', 'b', 'c'] },
      });

      await findBtnsByIcon(wrapper, 'remove_circle')[0]!.trigger('click');

      expect(formData.excluded_keys).toEqual(['b', 'c']);
    });
  });

  describe('required fields and loading state', () => {
    it('enables Save and Test parser when all required fields are filled', () => {
      const { wrapper } = mountForm();

      expect(getBtn(wrapper, 'Save').props('disable')).toBe(false);
      expect(getBtn(wrapper, 'Test parser').props('disable')).toBe(false);
    });

    it.each([
      ['name is null', { name: null }],
      ['name is empty', { name: '' }],
      ['timezone is missing', { timezone: null }],
      ['no timestamp key exists', { timestamp_keys: [] }],
    ])('disables Save and Test parser when %s', (_label, model) => {
      const { wrapper } = mountForm({ model });

      expect(getBtn(wrapper, 'Save').props('disable')).toBe(true);
      expect(getBtn(wrapper, 'Test parser').props('disable')).toBe(true);
    });

    it('does not require description, comment, measurement key or excluded keys', () => {
      const { wrapper } = mountForm({
        model: { description: null, comment: null, measurement_key: null, excluded_keys: [] },
      });

      expect(getBtn(wrapper, 'Save').props('disable')).toBe(false);
    });

    it('passes isLoading to the Save button', async () => {
      const { wrapper } = mountForm();

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(false);

      await wrapper.setProps({ isLoading: true } as Record<string, unknown>);

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(true);
    });

    it('applies the REQUIRED rule to permission group and timezone', () => {
      const { wrapper } = mountForm();

      expect(wrapper.findComponent(PermissionGroupSelectStub).props('rules')).toEqual([
        rules.REQUIRED,
      ]);
      expect(wrapper.findComponent(ParserTimezoneSelectStub).props('rules')).toEqual([
        rules.REQUIRED,
      ]);
    });
  });

  describe('submit and validation', () => {
    it('emits save exactly once for a valid form', async () => {
      const { wrapper } = mountForm();

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
      expect(wrapper.emitted('save')![0]).toEqual([]);
    });

    it.each([
      ['name is empty', { name: '' }],
      ['a timestamp key is empty', { timestamp_keys: [{ key: '', format: TIMESTAMP_FORMAT }] }],
      ['a timestamp key is null', { timestamp_keys: [{ key: null, format: TIMESTAMP_FORMAT }] }],
      ['a timestamp format is empty', { timestamp_keys: [{ key: 'Datetime', format: '' }] }],
      ['a timestamp format is null', { timestamp_keys: [{ key: 'Datetime', format: null }] }],
    ])('does not emit save when %s', async (_label, model) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toBeUndefined();
    });
  });

  describe('parser testing', () => {
    it('toggles the validation dialog with the test button', async () => {
      const { wrapper } = mountForm();
      const dialog = () => wrapper.findComponent(ParserValidateJsonStub);

      expect(dialog().props('modelValue')).toBe(false);
      expect(findBtn(wrapper, 'Test parser')).toBeDefined();
      expect(findBtn(wrapper, 'Close parser testing')).toBeUndefined();

      await getBtn(wrapper, 'Test parser').trigger('click');

      expect(dialog().props('modelValue')).toBe(true);
      expect(findBtn(wrapper, 'Test parser')).toBeUndefined();
      expect(findBtn(wrapper, 'Close parser testing')).toBeDefined();

      await getBtn(wrapper, 'Close parser testing').trigger('click');

      expect(dialog().props('modelValue')).toBe(false);
      expect(findBtn(wrapper, 'Test parser')).toBeDefined();
      expect(findBtn(wrapper, 'Close parser testing')).toBeUndefined();
    });

    it('closes when the dialog itself emits update:modelValue', async () => {
      const { wrapper } = mountForm();

      await getBtn(wrapper, 'Test parser').trigger('click');
      expect(wrapper.findComponent(ParserValidateJsonStub).props('modelValue')).toBe(true);

      wrapper.findComponent(ParserValidateJsonStub).vm.$emit('update:modelValue', false);
      await flushPromises();

      expect(wrapper.findComponent(ParserValidateJsonStub).props('modelValue')).toBe(false);
      expect(findBtn(wrapper, 'Test parser')).toBeDefined();
      expect(findBtn(wrapper, 'Close parser testing')).toBeUndefined();
    });

    it('initially passes a copy of the form data to the dialog', () => {
      const { wrapper, formData } = mountForm();

      expect(validatedData(wrapper)).toEqual(makeFormData());
      expect(validatedData(wrapper)).not.toBe(formData);
    });

    it('passes updated form data to the dialog once the form is valid', async () => {
      const { wrapper } = mountForm();

      await typeInto(findInput(wrapper, 'Name'), 'Renamed parser');
      await flushPromises();

      expect(validatedData(wrapper).name).toBe('Renamed parser');
    });

    it('keeps the last valid form data for the dialog while the form is invalid', async () => {
      const { wrapper } = mountForm();

      // all required fields are filled, but the timestamp format is empty -> form is invalid
      await typeInto(findInput(wrapper, 'Format (e.g.'), '');
      await flushPromises();

      expect(validatedData(wrapper).timestamp_keys[0]!.format).toBe(TIMESTAMP_FORMAT);
    });

    it('does not update the dialog data while a required field is missing', async () => {
      const { wrapper } = mountForm();

      await typeInto(findInput(wrapper, 'Name'), '');
      await flushPromises();

      expect(validatedData(wrapper).name).toBe('My parser');
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

    it('opens the pandas strftime docs in a new window', async () => {
      const { wrapper } = mountForm();

      await findBtnsByIcon(wrapper, 'help_outline')[0]!.trigger('click');

      expect(openSpy).toHaveBeenCalledTimes(1);
      expect(openSpy).toHaveBeenCalledWith(PANDAS_DOCS_URL, '_blank');
    });

    it('shows the docs tooltip for the help button', () => {
      const { wrapper } = mountForm();

      expect(wrapper.find('.tooltip').text()).toContain('View Pandas Docs');
    });
  });
});
