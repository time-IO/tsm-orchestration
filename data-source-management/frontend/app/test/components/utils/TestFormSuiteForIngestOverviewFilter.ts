// test/components/ingestFilterSuite.ts
import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { defineComponent, h, type Component, DefineComponent } from 'vue';
import { QBtn } from 'quasar';
import { findInput, nativeValue, typeInto } from './TestUtils'; // adjust path

installQuasarPlugin();

export interface IngestFilterConfig {
  /** Display name used in describe() */
  name: string;
  component: Component;
  /** Name of the type model, e.g. 'api_type' or 'ingest_type' */
  typeModel: string;
  /** Component name of the type select child, e.g. 'IngestTypeSelect' */
  typeSelectName: string;
  typeValue: string;
  otherTypeValue: string;
  emittedTypeValue: string;
}

const makeStub = (name: string, props: string[]) =>
  defineComponent({
    name,
    props,
    emits: ['update:modelValue'],
    setup: () => () => h('div', { class: `${name}-stub` }),
  }) as unknown as DefineComponent<Record<string, unknown>>;

export function describeIngestFilter(config: IngestFilterConfig) {
  const { typeModel } = config;

  // Child components have their own tests (and PermissionGroupSelect calls an API)
  const PermissionGroupSelectStub = makeStub('PermissionGroupSelect', [
    'modelValue',
    'label',
    'dense',
  ]);
  const TypeSelectStub = makeStub(config.typeSelectName, ['modelValue', 'dense']);
  const DateTimePickerStub = makeStub('DateTimePicker', [
    'modelValue',
    'label',
    'clearable',
    'dense',
  ]);

  const globalOptions = {
    stubs: {
      PermissionGroupSelect: PermissionGroupSelectStub,
      [config.typeSelectName]: TypeSelectStub,
      DateTimePicker: DateTimePickerStub,
    },
  };

  const FILLED = {
    name: 'My ingest',
    uuid: '123e4567-e89b-12d3-a456-426614174000',
    [typeModel]: config.typeValue,
    permission_group_id: 7,
    date_from: '2026-01-01T00:00:00',
    date_to: '2026-12-31T23:59:59',
  };

  const MODELS = [
    'name',
    'uuid',
    typeModel,
    'permission_group_id',
    'date_from',
    'date_to',
  ] as const;

  const mountFilter = (props: Record<string, unknown> = {}) =>
    mount(config.component, { props: { ...props }, global: globalOptions });

  const getDatePicker = (wrapper: ReturnType<typeof mountFilter>, label: string) => {
    const picker = wrapper
      .findAllComponents(DateTimePickerStub)
      .find((c) => c.props('label') === label);
    if (!picker) throw new Error(`DateTimePicker with label "${label}" not found`);
    return picker;
  };

  const getBtn = (wrapper: VueWrapper, text: string) => {
    const btn = wrapper.findAllComponents(QBtn).find((b) => b.text() === text);
    if (!btn) throw new Error(`QBtn with text "${text}" not found`);
    return btn;
  };

  describe(config.name, () => {
    describe('initialization', () => {
      it('shows empty inputs and unset child components without model values', () => {
        const wrapper = mountFilter();

        expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe('');
        expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe('');
        expect(
          wrapper.findComponent(PermissionGroupSelectStub).props('modelValue'),
        ).toBeUndefined();
        expect(wrapper.findComponent(TypeSelectStub).props('modelValue')).toBeUndefined();
        expect(getDatePicker(wrapper, 'Created at from').props('modelValue')).toBeUndefined();
        expect(getDatePicker(wrapper, 'Created at to').props('modelValue')).toBeUndefined();
      });

      it('shows the model values in the inputs and child components', () => {
        const wrapper = mountFilter(FILLED);

        expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe(FILLED.name);
        expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe(FILLED.uuid);
        expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(7);
        expect(wrapper.findComponent(TypeSelectStub).props('modelValue')).toBe(config.typeValue);
        expect(getDatePicker(wrapper, 'Created at from').props('modelValue')).toBe(
          FILLED.date_from,
        );
        expect(getDatePicker(wrapper, 'Created at to').props('modelValue')).toBe(FILLED.date_to);
      });
    });

    describe('prop changes', () => {
      it('updates inputs and child components when the models change from outside', async () => {
        const wrapper = mountFilter(FILLED);

        await wrapper.setProps({
          name: 'Other ingest',
          uuid: 'other-uuid',
          [typeModel]: config.otherTypeValue,
          permission_group_id: 9,
          date_from: '2025-01-01T00:00:00',
          date_to: '2025-12-31T23:59:59',
        });

        expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe('Other ingest');
        expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe('other-uuid');
        expect(wrapper.findComponent(TypeSelectStub).props('modelValue')).toBe(
          config.otherTypeValue,
        );
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
        const wrapper = mountFilter();

        await typeInto(findInput(wrapper, 'Filter by Name'), 'abc');
        await typeInto(findInput(wrapper, 'Filter by UUID'), '123');

        expect(wrapper.emitted('update:name')).toEqual([['abc']]);
        expect(wrapper.emitted('update:uuid')).toEqual([['123']]);
      });

      it('writes the child component values back to the matching models', async () => {
        const wrapper = mountFilter();

        wrapper.findComponent(PermissionGroupSelectStub).vm.$emit('update:modelValue', 5);
        wrapper
          .findComponent(TypeSelectStub)
          .vm.$emit('update:modelValue', config.emittedTypeValue);
        getDatePicker(wrapper, 'Created at from').vm.$emit(
          'update:modelValue',
          '2026-02-01T00:00:00',
        );
        getDatePicker(wrapper, 'Created at to').vm.$emit(
          'update:modelValue',
          '2026-03-01T00:00:00',
        );
        await flushPromises();

        expect(wrapper.emitted('update:permission_group_id')).toEqual([[5]]);
        expect(wrapper.emitted(`update:${typeModel}`)).toEqual([[config.emittedTypeValue]]);
        expect(wrapper.emitted('update:date_from')).toEqual([['2026-02-01T00:00:00']]);
        expect(wrapper.emitted('update:date_to')).toEqual([['2026-03-01T00:00:00']]);
      });
    });

    describe('apply filter', () => {
      it('emits applyFilters once when the apply button is clicked', async () => {
        const wrapper = mountFilter();

        await getBtn(wrapper, 'Apply filter').trigger('click');

        expect(wrapper.emitted('applyFilters')).toHaveLength(1);
      });

      it('emits applyFilters when Enter is pressed inside an input', async () => {
        const wrapper = mountFilter();

        await findInput(wrapper, 'Filter by Name').find('input').trigger('keyup', { key: 'Enter' });

        expect(wrapper.emitted('applyFilters')).toHaveLength(1);
      });

      it('does not emit applyFilters for other keys', async () => {
        const wrapper = mountFilter();

        await findInput(wrapper, 'Filter by Name').find('input').trigger('keyup', { key: 'a' });

        expect(wrapper.emitted('applyFilters')).toBeUndefined();
      });
    });

    describe('clear filter', () => {
      it('resets every model to undefined and emits applyFilters once', async () => {
        const wrapper = mountFilter(FILLED);

        await getBtn(wrapper, 'Clear filter').trigger('click');

        for (const model of MODELS) {
          expect(wrapper.emitted(`update:${model}`), model).toEqual([[undefined]]);
        }
        expect(wrapper.emitted('applyFilters')).toHaveLength(1);
      });

      it('clears the inputs and child components', async () => {
        const wrapper = mountFilter(FILLED);

        await getBtn(wrapper, 'Clear filter').trigger('click');
        await flushPromises();

        expect(nativeValue(findInput(wrapper, 'Filter by Name'))).toBe('');
        expect(nativeValue(findInput(wrapper, 'Filter by UUID'))).toBe('');
        expect(
          wrapper.findComponent(PermissionGroupSelectStub).props('modelValue'),
        ).toBeUndefined();
        expect(wrapper.findComponent(TypeSelectStub).props('modelValue')).toBeUndefined();
        expect(getDatePicker(wrapper, 'Created at from').props('modelValue')).toBeUndefined();
        expect(getDatePicker(wrapper, 'Created at to').props('modelValue')).toBeUndefined();
      });

      it('still emits applyFilters when no filter is set', async () => {
        const wrapper = mountFilter();

        await getBtn(wrapper, 'Clear filter').trigger('click');

        expect(wrapper.emitted('applyFilters')).toHaveLength(1);
      });

      it('emits the model updates before applyFilters', async () => {
        const calls: string[] = [];
        const wrapper = mountFilter({
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
        const wrapper = mountFilter({ uuid: '  123e4567  ' });

        findInput(wrapper, 'Filter by UUID').vm.$emit('blur');
        await flushPromises();

        expect(wrapper.emitted('update:uuid')).toEqual([['123e4567']]);
      });

      it('does not emit anything on blur when the uuid is empty', async () => {
        const wrapper = mountFilter();

        findInput(wrapper, 'Filter by UUID').vm.$emit('blur');
        await flushPromises();

        expect(wrapper.emitted('update:uuid')).toBeUndefined();
      });
    });
  });
}
