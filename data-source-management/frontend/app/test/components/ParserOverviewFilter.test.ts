import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { QBtn} from 'quasar';
import { describe, expect, it } from 'vitest';
import { defineComponent, h } from 'vue';

import ParserOverviewFilter from '@/components/ParserOverviewFilter.vue'; // adjust path
import { findInput, nativeValue, typeInto } from './utils/TestUtilsParser';

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

// The child components have their own tests (and PermissionGroupSelect calls an API)
const PermissionGroupSelectStub = defineComponent({
  name: 'PermissionGroupSelect',
  props: ['modelValue', 'label', 'dense'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'permission-group-select-stub' }),
});

const ParserTypeSelectStub = defineComponent({
  name: 'ParserTypeSelect',
  props: ['modelValue', 'dense'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'parser-type-select-stub' }),
});

const DateTimePickerStub = defineComponent({
  name: 'DateTimePicker',
  props: ['modelValue', 'label', 'clearable', 'dense'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'date-time-picker-stub' }),
});

const globalOptions = {
  stubs: {
    PermissionGroupSelect: PermissionGroupSelectStub,
    ParserTypeSelect: ParserTypeSelectStub,
    DateTimePicker: DateTimePickerStub,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const FILLED = {
  name: 'My parser',
  uuid: '123e4567-e89b-12d3-a456-426614174000',
  parser_type: 'csv',
  permission_group_id: 7,
  date_from: '2026-01-01T00:00:00',
  date_to: '2026-12-31T23:59:59',
};

const MODELS = [
  'name',
  'uuid',
  'parser_type',
  'permission_group_id',
  'date_from',
  'date_to',
] as const;

const mountParserFilter = (props: Record<string, unknown> = {}) =>
  mount(ParserOverviewFilter, {
    props: { ...props },
    global: globalOptions,
  });

const getBtn = (wrapper: VueWrapper, text: string) => {
  const btn = wrapper.findAllComponents(QBtn).find((b) => b.text() === text);
  if (!btn) throw new Error(`QBtn "${text}" not found`);
  return btn;
};

const getDatePicker = (wrapper: VueWrapper, label: string) => {
  const picker = wrapper
    .findAllComponents(DateTimePickerStub)
    .find((c) => c.props('label') === label);
  if (!picker) throw new Error(`DateTimePicker with label "${label}" not found`);
  return picker;
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ParserFilter', () => {
  describe('initialization', () => {
    it('shows empty inputs and unset child components without model values', () => {
      const wrapper = mountParserFilter();

      expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe('');
      expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe('');
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBeUndefined();
      expect(wrapper.findComponent(ParserTypeSelectStub).props('modelValue')).toBeUndefined();
      expect(getDatePicker(wrapper, 'Created at from').props('modelValue')).toBeUndefined();
      expect(getDatePicker(wrapper, 'Created at to').props('modelValue')).toBeUndefined();
    });

    it('shows the model values in the inputs and child components', () => {
      const wrapper = mountParserFilter(FILLED);

      expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe(FILLED.name);
      expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe(FILLED.uuid);
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(7);
      expect(wrapper.findComponent(ParserTypeSelectStub).props('modelValue')).toBe('csv');
      expect(getDatePicker(wrapper, 'Created at from').props('modelValue')).toBe(FILLED.date_from);
      expect(getDatePicker(wrapper, 'Created at to').props('modelValue')).toBe(FILLED.date_to);
    });
  });

  describe('prop changes', () => {
    it('updates inputs and child components when the models change from outside', async () => {
      const wrapper = mountParserFilter(FILLED);

      await wrapper.setProps({
        name: 'Other parser',
        uuid: 'other-uuid',
        parser_type: 'json',
        permission_group_id: 9,
        date_from: '2025-01-01T00:00:00',
        date_to: '2025-12-31T23:59:59',
      });

      expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe('Other parser');
      expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe('other-uuid');
      expect(wrapper.findComponent(ParserTypeSelectStub).props('modelValue')).toBe('json');
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(9);
      expect(getDatePicker(wrapper, 'Created at from').props('modelValue')).toBe(
        '2025-01-01T00:00:00',
      );
      expect(getDatePicker(wrapper, 'Created at to').props('modelValue')).toBe(
        '2025-12-31T23:59:59',
      );
    });
  });

  describe('v-model', () => {
    it('emits update:name and update:uuid when typing', async () => {
      const wrapper = mountParserFilter();

      await typeInto(findInput(wrapper, 'Filter by Name'), 'abc');
      await typeInto(findInput(wrapper, 'Filter by UUID'), '123');

      expect(wrapper.emitted('update:name')).toEqual([['abc']]);
      expect(wrapper.emitted('update:uuid')).toEqual([['123']]);
    });

    it('writes the child component values back to the matching models', async () => {
      const wrapper = mountParserFilter();

      wrapper.findComponent(PermissionGroupSelectStub).vm.$emit('update:modelValue', 5);
      wrapper.findComponent(ParserTypeSelectStub).vm.$emit('update:modelValue', 'soilcan');
      getDatePicker(wrapper, 'Created at from').vm.$emit('update:modelValue', '2026-02-01T00:00:00');
      getDatePicker(wrapper, 'Created at to').vm.$emit('update:modelValue', '2026-03-01T00:00:00');
      await flushPromises();

      expect(wrapper.emitted('update:permission_group_id')).toEqual([[5]]);
      expect(wrapper.emitted('update:parser_type')).toEqual([['soilcan']]);
      expect(wrapper.emitted('update:date_from')).toEqual([['2026-02-01T00:00:00']]);
      expect(wrapper.emitted('update:date_to')).toEqual([['2026-03-01T00:00:00']]);
    });
  });

  describe('apply filter', () => {
    it('emits applyFilters once when the apply button is clicked', async () => {
      const wrapper = mountParserFilter();

      await getBtn(wrapper, 'Apply filter').trigger('click');

      expect(wrapper.emitted('applyFilters')).toHaveLength(1);
    });

    it('emits applyFilters when Enter is pressed inside an input', async () => {
      const wrapper = mountParserFilter();

      await findInput(wrapper, 'Filter by Name').find('input').trigger('keyup', { key: 'Enter' });

      expect(wrapper.emitted('applyFilters')).toHaveLength(1);
    });

    it('does not emit applyFilters for other keys', async () => {
      const wrapper = mountParserFilter();

      await findInput(wrapper, 'Filter by Name').find('input').trigger('keyup', { key: 'a' });

      expect(wrapper.emitted('applyFilters')).toBeUndefined();
    });
  });

  describe('clear filter', () => {
    it('resets every model to undefined and emits applyFilters once', async () => {
      const wrapper = mountParserFilter(FILLED);

      await getBtn(wrapper, 'Clear filter').trigger('click');

      for (const model of MODELS) {
        expect(wrapper.emitted(`update:${model}`), model).toEqual([[undefined]]);
      }
      expect(wrapper.emitted('applyFilters')).toHaveLength(1);
    });

    it('clears the inputs and child components', async () => {
      const wrapper = mountParserFilter(FILLED);

      await getBtn(wrapper, 'Clear filter').trigger('click');
      await flushPromises();

      expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe('');
      expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe('');
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBeUndefined();
      expect(wrapper.findComponent(ParserTypeSelectStub).props('modelValue')).toBeUndefined();
      expect(getDatePicker(wrapper, 'Created at from').props('modelValue')).toBeUndefined();
      expect(getDatePicker(wrapper, 'Created at to').props('modelValue')).toBeUndefined();
    });

    it('still emits applyFilters when no filter is set', async () => {
      const wrapper = mountParserFilter();

      await getBtn(wrapper, 'Clear filter').trigger('click');

      expect(wrapper.emitted('applyFilters')).toHaveLength(1);
    });

    it('emits the model updates before applyFilters', async () => {
      const calls: string[] = [];
      const wrapper = mountParserFilter({
        ...FILLED,
        'onUpdate:name': () => calls.push('update:name'),
        onApplyFilters: () => calls.push('applyFilters'),
      });

      await getBtn(wrapper, 'Clear filter').trigger('click');

      // the parent must see the cleared values when it handles applyFilters
      expect(calls).toEqual(['update:name', 'applyFilters']);
    });
  });

  describe('uuid trimming', () => {
    it('trims surrounding whitespace when the uuid input loses focus', async () => {
      const wrapper = mountParserFilter({ uuid: '  123e4567  ' });

      findInput(wrapper, 'Filter by UUID').vm.$emit('blur');
      await flushPromises();

      expect(wrapper.emitted('update:uuid')).toEqual([['123e4567']]);
    });

    it('does not emit anything on blur when the uuid is empty', async () => {
      const wrapper = mountParserFilter();

      findInput(wrapper, 'Filter by UUID').vm.$emit('blur');
      await flushPromises();

      expect(wrapper.emitted('update:uuid')).toBeUndefined();
    });
  });
});
