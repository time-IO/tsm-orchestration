import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { QBtn, QInput, QSelect, QToggle } from 'quasar';
import { describe, expect, it } from 'vitest';
import { defineComponent, h, reactive } from 'vue';

import ParserFormSoilcan from '@/components/ParserFormSoilcan.vue'; // adjust path
import type { SoilcanParserUpdate } from '@/services/parser_soilcan/types'; // adjust path
import {
  findInput,
  getBtn,
  nativeValue,
  QPageStub,
  submit,
  typeInto,
} from './utils/TestUtilsParser';

// Same shape as the local type in ParserFormSoilcan.vue
type SoilcanParserFormData = SoilcanParserUpdate & {
  permission_group_id?: number | null;
};

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

const PermissionGroupSelectStub = defineComponent({
  name: 'PermissionGroupSelect',
  props: ['modelValue', 'disable', 'rules'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'permission-group-select-stub' }),
});

const globalOptions = {
  stubs: {
    QPage: QPageStub,
    PermissionGroupSelect: PermissionGroupSelectStub,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TYPE_OPTIONS = ['operating-parameters', 'sensor-data', 'weighing-data'];

const makeFormData = (overrides: Partial<SoilcanParserFormData> = {}): SoilcanParserFormData => ({
  permission_group_id: 1,
  name: 'My parser',
  description: null,
  type: 'sensor-data',
  header: false,
  ...overrides,
});

type MountOptions = {
  model?: Partial<SoilcanParserFormData>;
  props?: Record<string, unknown>;
};

// The model is reactive so that the component's v-model mutations (formData.value.x = ...)
// are visible in the test and also trigger a re-render.
function mountForm({ model, props }: MountOptions = {}) {
  const formData = reactive(makeFormData(model)) as SoilcanParserFormData;
  const wrapper = mount(ParserFormSoilcan, {
    props: {
      title: 'New SoilCan Parser',
      isLoading: false,
      backRoute: '/parser/new',
      modelValue: formData,
      ...props,
    },
    global: globalOptions,
  });
  return { wrapper, formData };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ParserFormSoilcan', () => {
  describe('initialization and props', () => {
    it('renders the title and passes backRoute to the back button', () => {
      const { wrapper } = mountForm({
        props: { title: 'Edit SoilCan Parser', backRoute: '/parser/soilcan/5' },
      });

      expect(wrapper.find('h5').text()).toBe('Edit SoilCan Parser');
      expect(getBtn(wrapper, 'back').props('to')).toBe('/parser/soilcan/5');
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

    it('shows the initial model values in the form controls', () => {
      const { wrapper } = mountForm({
        model: {
          name: 'Parser A',
          description: 'Some description',
          type: 'weighing-data',
          header: true,
          permission_group_id: 7,
        },
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('Parser A');
      expect(nativeValue(findInput(wrapper, 'Description'))).toBe('Some description');
      expect(wrapper.findComponent(QSelect).props('modelValue')).toBe('weighing-data');
      expect(wrapper.findComponent(QSelect).text()).toContain('weighing-data');
      expect(wrapper.findComponent(QToggle).props('modelValue')).toBe(true);
      expect(wrapper.findComponent(PermissionGroupSelectStub).props('modelValue')).toBe(7);
    });

    it('offers the three SoilCan parser types', () => {
      const { wrapper } = mountForm();

      expect(wrapper.findComponent(QSelect).props('options')).toEqual(TYPE_OPTIONS);
    });

    it('falls back to an empty default model when no v-model is passed', () => {
      const wrapper = mount(ParserFormSoilcan, {
        props: { title: 'New', isLoading: false, backRoute: '/back' },
        global: globalOptions,
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('');
      expect(wrapper.findComponent(QSelect).props('modelValue')).toBe('');
      expect(wrapper.findComponent(QToggle).props('modelValue')).toBe(false);
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

    // The select is stubbed, so its rule is not part of the form validation.
    // Therefore the rule passed to it is verified directly.
    it('requires a permission group via the rule passed to the select', () => {
      const { wrapper } = mountForm();
      const [rule] = wrapper.findComponent(PermissionGroupSelectStub).props('rules') as Array<
        (val: unknown) => true | string
      >;

      expect(rule!(null)).toBe('Permission Group is required');
      expect(rule!(3)).toBe(true);
    });
  });

  describe('v-model', () => {
    it('writes name and description back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Name'), 'New name');
      await typeInto(findInput(wrapper, 'Description'), 'New description');

      expect(formData.name).toBe('New name');
      expect(formData.description).toBe('New description');
    });

    it('writes the selected type back to the model', async () => {
      const { wrapper, formData } = mountForm({ model: { type: '' } });

      wrapper.findComponent(QSelect).vm.$emit('update:modelValue', 'operating-parameters');
      await flushPromises();

      expect(formData.type).toBe('operating-parameters');
      expect(wrapper.findComponent(QSelect).props('modelValue')).toBe('operating-parameters');
    });

    it('toggles header on and off with the toggle', async () => {
      const { wrapper, formData } = mountForm({ model: { header: false } });

      await wrapper.findComponent(QToggle).trigger('click');
      expect(formData.header).toBe(true);

      await wrapper.findComponent(QToggle).trigger('click');
      expect(formData.header).toBe(false);
    });
  });

  describe('loading state', () => {
    it('passes isLoading to the Save button', async () => {
      const { wrapper } = mountForm();

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(false);

      await wrapper.setProps({ isLoading: true } as Record<string, unknown>);

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(true);
    });

    it('does not disable Save for an invalid form (validation happens on submit)', () => {
      const { wrapper } = mountForm({ model: { name: '', type: '' } });

      expect(getBtn(wrapper, 'Save').props('disable')).toBe(false);
    });
  });

  describe('submit and validation', () => {
    it('emits save exactly once for a valid form', async () => {
      const { wrapper } = mountForm();

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
      expect(wrapper.emitted('save')![0]).toEqual([]);
    });

    it('accepts a name with exactly 80 characters and no description', async () => {
      const { wrapper } = mountForm({ model: { name: 'a'.repeat(80), description: null } });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });

    it.each([
      ['name is empty', { name: '' }, 'Name is required'],
      ['name is longer than 80 characters', { name: 'a'.repeat(81) }, 'Maximum 80 characters'],
      ['type is empty', { type: '' }, 'Type is required'],
    ])('blocks save and shows an error when %s', async (_label, model, message) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toBeUndefined();
      expect(wrapper.text()).toContain(message);
    });
  });
});
