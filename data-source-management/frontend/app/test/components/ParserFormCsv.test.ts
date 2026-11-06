import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { QBtn, QInput } from 'quasar';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, reactive } from 'vue';

import ParserFormCsv from '@/components/ParserFormCsv.vue'; // adjust path
import type { CsvParserFormData } from '@/utils/parser_csv_utils';
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

const { parseJsonFieldMock, toNullableNumberMock } = vi.hoisted(() => ({
  parseJsonFieldMock: vi.fn(),
  toNullableNumberMock: vi.fn(),
}));

vi.mock('@/utils/string_utils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/utils/string_utils')>();
  return {
    ...actual,
    parseJsonField: parseJsonFieldMock,
    toNullableNumber: toNullableNumberMock,
  };
});

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

const ParserEncodingSelectStub = defineComponent({
  name: 'ParserEncodingSelect',
  props: ['modelValue', 'rules'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'encoding-select-stub' }),
});

const ParserValidateCsvStub = defineComponent({
  name: 'ParserValidateCsv',
  props: ['modelValue', 'formData'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'parser-validate-csv-stub' }),
});

const globalOptions = {
  stubs: {
    QPage: QPageStub,
    QTooltip: QTooltipStub,
    PermissionGroupSelect: PermissionGroupSelectStub,
    ParserTimezoneSelect: ParserTimezoneSelectStub,
    ParserEncodingSelect: ParserEncodingSelectStub,
    ParserValidateCsv: ParserValidateCsvStub,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S';
const PANDAS_DOCS_URL = 'https://pandas.pydata.org/docs/reference/api/pandas.Period.strftime.html';

const makeFormData = (overrides: Partial<CsvParserFormData> = {}): CsvParserFormData => ({
  permission_group_id: 1,
  name: 'My parser',
  description: null,
  delimiter: ',',
  headlines_to_exclude: null,
  footlines_to_exclude: 0,
  pandas_read_csv: null,
  timestamp_columns: [{ column: 1, timestamp_format: TIMESTAMP_FORMAT }],
  comment: [],
  header: 1,
  timezone: 'UTC',
  encoding: 'utf-8',
  ...overrides,
});

type MountOptions = {
  model?: Partial<CsvParserFormData>;
  props?: Record<string, unknown>;
};

// The model is reactive so that the component's v-model mutations (formData.value.x = ...)
// are visible in the test and also trigger a re-render.
function mountForm({ model, props }: MountOptions = {}) {
  const formData = reactive(makeFormData(model)) as CsvParserFormData;
  const wrapper = mount(ParserFormCsv, {
    props: {
      title: 'New CSV Parser',
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
  wrapper.findComponent(ParserValidateCsvStub).props('formData') as CsvParserFormData;

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ParserFormCsv', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    parseJsonFieldMock.mockReturnValue(null);
    toNullableNumberMock.mockImplementation((v: unknown) =>
      v === '' || v == null ? null : Number(v),
    );
  });

  describe('initialization and props', () => {
    it('renders the title and passes backRoute to the back button', () => {
      const { wrapper } = mountForm({
        props: { title: 'Edit CSV Parser', backRoute: '/parser/csv/5' },
      });

      expect(wrapper.find('h5').text()).toBe('Edit CSV Parser');
      expect(getBtn(wrapper, 'back').props('to')).toBe('/parser/csv/5');
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

    it('shows the initial model values in the inputs and selects', () => {
      const { wrapper } = mountForm({
        model: {
          name: 'Parser A',
          description: 'Some description',
          delimiter: ';',
          headlines_to_exclude: '1,2',
          footlines_to_exclude: 3,
          header: 2,
          pandas_read_csv: '{"skiprows": 1}',
          permission_group_id: 7,
          timezone: 'Europe/Berlin',
          encoding: 'latin-1',
        },
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('Parser A');
      expect(nativeValue(findInput(wrapper, 'Description'))).toBe('Some description');
      expect(nativeValue(findInput(wrapper, 'Column delimiter'))).toBe(';');
      expect(nativeValue(findInput(wrapper, 'Number of headlines'))).toBe('1,2');
      expect(nativeValue(findInput(wrapper, 'Number of footlines'))).toBe('3');
      expect(nativeValue(findInput(wrapper, 'Header row index'))).toBe('2');
      expect(nativeValue(findInput(wrapper, 'Pandas read csv'))).toBe('{"skiprows": 1}');
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(7);
      expect(wrapper.findComponent(ParserTimezoneSelectStub).props('modelValue')).toBe(
        'Europe/Berlin',
      );
      expect(wrapper.findComponent(ParserEncodingSelectStub).props('modelValue')).toBe('latin-1');
    });

    it('renders one block per timestamp column and comment character', () => {
      const { wrapper } = mountForm({
        model: {
          timestamp_columns: [
            { column: 0, timestamp_format: '%Y' },
            { column: 3, timestamp_format: '%H' },
          ],
          comment: ['#', '//', ';'],
        },
      });

      expect(wrapper.text()).toContain('Timestamp Column 1'); // Template: Timestamp Column {{ idx + 1 }}
      expect(wrapper.text()).toContain('Timestamp Column 2');
      expect(wrapper.text()).not.toContain('Timestamp Column 3');
      expect(findInputs(wrapper, 'Column index')).toHaveLength(2);
      expect(findInputs(wrapper, 'Comment character').map(nativeValue)).toEqual(['#', '//', ';']);
    });

    it('falls back to an empty default model when no v-model is passed', () => {
      const wrapper = mount(ParserFormCsv, {
        props: { title: 'New', isLoading: false, backRoute: '/back' },
        global: globalOptions,
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('');
      expect(nativeValue(findInput(wrapper, 'Number of footlines'))).toBe('0');
      expect(wrapper.text()).toContain('At least one timestamp column is required');
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

  describe('v-model', () => {
    it('writes name, description and delimiter back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Name'), 'New name');
      await typeInto(findInput(wrapper, 'Description'), 'New description');
      await typeInto(findInput(wrapper, 'Column delimiter'), '\t');

      expect(formData.name).toBe('New name');
      expect(formData.description).toBe('New description');
      expect(formData.delimiter).toBe('\t');
    });

    it('trims the headlines_to_exclude value', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Number of headlines'), '  1, 2  ');

      expect(formData.headlines_to_exclude).toBe('1, 2');
    });

    it('stores footlines_to_exclude as a number', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Number of footlines'), '3');

      expect(formData.footlines_to_exclude).toBe(3);
    });

    it('converts the header input with toNullableNumber', async () => {
      const { wrapper, formData } = mountForm();

      toNullableNumberMock.mockReturnValueOnce(42);
      await typeInto(findInput(wrapper, 'Header row index'), '7');

      expect(toNullableNumberMock).toHaveBeenCalledWith('7');
      expect(formData.header).toBe(42);

      toNullableNumberMock.mockReturnValueOnce(null);
      await typeInto(findInput(wrapper, 'Header row index'), '');

      expect(formData.header).toBeNull();
    });

    it('writes the pandas_read_csv textarea back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Pandas read csv'), '{"skiprows": 2}');

      expect(formData.pandas_read_csv).toBe('{"skiprows": 2}');
    });

    it('writes timezone and encoding from the selects back to the model', async () => {
      const { wrapper, formData } = mountForm();

      wrapper
        .findComponent(ParserTimezoneSelectStub)
        .vm.$emit('update:modelValue', 'Europe/Berlin');
      wrapper.findComponent(ParserEncodingSelectStub).vm.$emit('update:modelValue', 'latin-1');

      expect(formData.timezone).toBe('Europe/Berlin');
      expect(formData.encoding).toBe('latin-1');
    });

    it('writes the permission group back to the model', () => {
      const { wrapper, formData } = mountForm();

      wrapper.findComponent(PermissionGroupSelectStub).vm.$emit('update:modelValue', 5);

      expect(formData.permission_group_id).toBe(5);
    });

    it('ignores permission group changes when disablePermissionGroup is true', () => {
      const { wrapper, formData } = mountForm({
        props: { disablePermissionGroup: true },
        model: { permission_group_id: 1 },
      });

      wrapper.findComponent(PermissionGroupSelectStub).vm.$emit('update:modelValue', 5);

      expect(formData.permission_group_id).toBe(1);
    });
  });

  describe('timestamp columns', () => {
    it('adds an empty timestamp column', async () => {
      const { wrapper, formData } = mountForm();

      await getBtn(wrapper, 'Add timestamp column').trigger('click');

      expect(formData.timestamp_columns).toEqual([
        { column: 1, timestamp_format: TIMESTAMP_FORMAT },
        { column: null, timestamp_format: null },
      ]);
      expect(wrapper.text()).toContain('Timestamp Column 2');
    });

    it('removes exactly the clicked timestamp column', async () => {
      const { wrapper, formData } = mountForm({
        model: {
          timestamp_columns: [
            { column: 0, timestamp_format: 'a' },
            { column: 1, timestamp_format: 'b' },
            { column: 2, timestamp_format: 'c' },
          ],
        },
      });

      await findBtnsByIcon(wrapper, 'remove_circle')[1]!.trigger('click');

      expect(formData.timestamp_columns).toEqual([
        { column: 0, timestamp_format: 'a' },
        { column: 2, timestamp_format: 'c' },
      ]);
      expect(wrapper.text()).not.toContain('Timestamp Column 3');
    });

    it('writes column index (as number) and format back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Column index'), '4');
      await typeInto(findInput(wrapper, 'Timestamp format'), '%d.%m.%Y');

      expect(formData.timestamp_columns[0]).toEqual({ column: 4, timestamp_format: '%d.%m.%Y' });
    });

    it('shows the hint only while no timestamp column exists', async () => {
      const { wrapper } = mountForm({ model: { timestamp_columns: [] } });
      const hint = 'At least one timestamp column is required';

      expect(wrapper.text()).toContain(hint);

      await getBtn(wrapper, 'Add timestamp column').trigger('click');

      expect(wrapper.text()).not.toContain(hint);
    });
  });

  describe('comment characters', () => {
    it('adds an empty comment character', async () => {
      const { wrapper, formData } = mountForm();

      await getBtn(wrapper, 'Add comment character').trigger('click');

      expect(formData.comment).toEqual(['']);
      expect(wrapper.text()).toContain('Comment Character 1');
    });

    it('writes a comment character back to the model', async () => {
      const { wrapper, formData } = mountForm({ model: { comment: [''] } });

      await typeInto(findInput(wrapper, 'Comment character'), '#');

      expect(formData.comment).toEqual(['#']);
    });

    it('removes exactly the clicked comment character', async () => {
      // no timestamp columns, so only the comment buttons carry the "remove_circle" icon
      const { wrapper, formData } = mountForm({
        model: { timestamp_columns: [], comment: ['#', ';', '//'] },
      });

      await findBtnsByIcon(wrapper, 'remove_circle')[0]!.trigger('click');

      expect(formData.comment).toEqual([';', '//']);
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
      ['delimiter is missing', { delimiter: null }],
      ['timezone is missing', { timezone: null }],
      ['encoding is missing', { encoding: null }],
      ['no timestamp column exists', { timestamp_columns: [] }],
    ])('disables Save and Test parser when %s', (_label, model) => {
      const { wrapper } = mountForm({ model });

      expect(getBtn(wrapper, 'Save').props('disable')).toBe(true);
      expect(getBtn(wrapper, 'Test parser').props('disable')).toBe(true);
    });

    it('passes isLoading to the Save button', async () => {
      const { wrapper } = mountForm();

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(false);

      await wrapper.setProps({ isLoading: true } as Record<string, unknown>);

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(true);
    });

    it('applies the REQUIRED rule to permission group, timezone and encoding', () => {
      const { wrapper } = mountForm();

      expect(wrapper.findComponent(PermissionGroupSelectStub).props('rules')).toEqual([
        rules.REQUIRED,
      ]);
      expect(wrapper.findComponent(ParserTimezoneSelectStub).props('rules')).toEqual([
        rules.REQUIRED,
      ]);
      expect(wrapper.findComponent(ParserEncodingSelectStub).props('rules')).toEqual([
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
      ['name is longer than 80 characters', { name: 'a'.repeat(81) }],
      ['delimiter is empty', { delimiter: '' }],
      ['a timestamp format is empty', { timestamp_columns: [{ column: 1, timestamp_format: '' }] }],
      [
        'a timestamp column index is missing',
        { timestamp_columns: [{ column: null, timestamp_format: TIMESTAMP_FORMAT }] },
      ],
    ])('does not emit save when %s', async (_label, model) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toBeUndefined();
    });

    it('accepts 0 as timestamp column index and as header row', async () => {
      const { wrapper } = mountForm({
        model: {
          header: 0,
          timestamp_columns: [{ column: 0, timestamp_format: TIMESTAMP_FORMAT }],
        },
      });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });

    it('validates pandas_read_csv with parseJsonField and shows its error message', async () => {
      parseJsonFieldMock.mockImplementation(() => {
        throw new Error('Invalid JSON: unexpected token');
      });
      const { wrapper } = mountForm({ model: { pandas_read_csv: '{bad' } });

      await submit(wrapper);

      expect(parseJsonFieldMock).toHaveBeenCalledWith('{bad');
      expect(wrapper.text()).toContain('Invalid JSON: unexpected token');
      expect(wrapper.emitted('save')).toBeUndefined();
    });

    it('shows a fallback message when parseJsonField throws a non-Error', async () => {
      parseJsonFieldMock.mockImplementation(() => {
        throw 'boom';
      });
      const { wrapper } = mountForm({ model: { pandas_read_csv: '{bad' } });

      await submit(wrapper);

      expect(wrapper.text()).toContain('Pandas read csv must contain valid JSON');
      expect(wrapper.emitted('save')).toBeUndefined();
    });

    it('emits save when pandas_read_csv contains valid JSON', async () => {
      const { wrapper } = mountForm({ model: { pandas_read_csv: '{"skiprows": 1}' } });

      await submit(wrapper);

      expect(parseJsonFieldMock).toHaveBeenCalledWith('{"skiprows": 1}');
      expect(wrapper.emitted('save')).toHaveLength(1);
    });
  });

  describe('parser testing', () => {
    it('toggles the validation dialog with the test button', async () => {
      const { wrapper } = mountForm();
      const dialog = () => wrapper.findComponent(ParserValidateCsvStub);

      expect(dialog().props('modelValue')).toBe(false);
      expect(findBtn(wrapper, 'Test parser')).toBeDefined();
      expect(findBtn(wrapper, 'Close parser testing')).toBeUndefined();

      await getBtn(wrapper, 'Test parser').trigger('click');

      expect(dialog().props('modelValue')).toBe(true);
      expect(findBtn(wrapper, 'Test parser')).toBeUndefined();

      await getBtn(wrapper, 'Close parser testing').trigger('click');

      expect(dialog().props('modelValue')).toBe(false);
      expect(findBtn(wrapper, 'Test parser')).toBeDefined();
    });

    it('closes when the dialog itself emits update:modelValue', async () => {
      const { wrapper } = mountForm();

      await getBtn(wrapper, 'Test parser').trigger('click');
      expect(wrapper.findComponent(ParserValidateCsvStub).props('modelValue')).toBe(true);

      wrapper.findComponent(ParserValidateCsvStub).vm.$emit('update:modelValue', false);
      await flushPromises();

      expect(wrapper.findComponent(ParserValidateCsvStub).props('modelValue')).toBe(false);
      expect(findBtn(wrapper, 'Test parser')).toBeDefined();
      expect(findBtn(wrapper, 'Close parser testing')).toBeUndefined();
    });

    it('initially passes a copy of the form data to the dialog', () => {
      const { wrapper, formData } = mountForm();

      expect(validatedData(wrapper)).toEqual(makeFormData());
      expect(validatedData(wrapper)).not.toBe(formData); //not the same object, but copy
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
      await typeInto(findInput(wrapper, 'Timestamp format'), '');
      await flushPromises();

      expect(validatedData(wrapper).timestamp_columns[0]!.timestamp_format).toBe(TIMESTAMP_FORMAT);
    });

    it('does not update the dialog data while a required field is missing', async () => {
      const { wrapper } = mountForm();

      await typeInto(findInput(wrapper, 'Column delimiter'), '');
      await flushPromises();

      expect(validatedData(wrapper).delimiter).toBe(',');
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

    it('links to the wiki in a new tab', () => {
      const { wrapper } = mountForm();

      const link = wrapper.find('a[target="_blank"]');

      expect(link.attributes('href')).toContain('TimeIO-Frontend#csv-parser');
    });
  });
});
