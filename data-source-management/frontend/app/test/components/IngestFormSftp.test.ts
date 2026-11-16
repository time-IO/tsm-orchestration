import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { defineComponent, h, reactive } from 'vue';

import IngestFormSftp from '@/components/IngestFormSftp.vue';
import type { IngestSftpCreate } from '@/services/ingest_sftp/types';
import type { PermissionGroup } from '@/services/permission_group/types';
import type { ParserRead } from '@/services/types';
import { rules } from '@/utils/validation/rules';
import { findInput, getBtn, nativeValue, QPageStub, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

const PermissionGroupSelectStub = defineComponent({
  name: 'PermissionGroupSelect',
  props: ['modelValue', 'preselectedItem', 'rules'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'permission-group-select-stub' }),
});

const ParserSelectByTypeStub = defineComponent({
  name: 'ParserSelectByType',
  props: ['modelValue', 'permissionGroupId', 'disable', 'preselectedParser', 'rules'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'parser-select-by-type-stub' }),
});

const HelpButtonStub = defineComponent({
  name: 'HelpButton',
  props: ['titleHelp', 'textHelp', 'termHelp'],
  setup: () => () => h('div', { class: 'help-button-stub' }),
});

const globalOptions = {
  stubs: {
    QPage: QPageStub,
    PermissionGroupSelect: PermissionGroupSelectStub,
    ParserSelectByType: ParserSelectByTypeStub,
    HelpButton: HelpButtonStub,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeFormData = (overrides: Partial<IngestSftpCreate> = {}): IngestSftpCreate => ({
  permission_group_id: 1,
  name: 'My ingest',
  description: null,
  parser_id: 2,
  filename_pattern: '*.csv',
  ...overrides,
});

type MountOptions = {
  model?: Partial<IngestSftpCreate>;
  props?: Record<string, unknown>;
};

// The model is reactive so that the component's v-model mutations (formData.value.x = ...)
// are visible in the test and also trigger a re-render.
const mountForm = ({ model = {}, props = {} }: MountOptions = {}) => {
  const formData = reactive(makeFormData(model));
  const wrapper = mount(IngestFormSftp, {
    props: {
      title: 'New SFTP ingest',
      isLoading: false,
      backRoute: '/ingest/new',
      modelValue: formData,
      ...props,
    },
    global: globalOptions,
  });
  return { wrapper, formData };
};

const permissionSelect = (w: VueWrapper) => w.findComponent(PermissionGroupSelectStub);
const parserSelect = (w: VueWrapper) => w.findComponent(ParserSelectByTypeStub);

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('IngestFormSftp', () => {
  describe('initialization', () => {
    it('shows the title and passes backRoute to the back button', () => {
      const { wrapper } = mountForm({ props: { title: 'Copy ingest', backRoute: '/ingest/7' } });

      expect(wrapper.find('h5').text()).toBe('Copy ingest');
      expect(getBtn(wrapper, 'back').props('to')).toBe('/ingest/7');
    });

    it('shows the model values in the inputs and selects', () => {
      const { wrapper } = mountForm({
        model: { description: 'Some text', permission_group_id: 4, parser_id: 8 },
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('My ingest');
      expect(nativeValue(findInput(wrapper, 'Description'))).toBe('Some text');
      expect(nativeValue(findInput(wrapper, 'Filename pattern'))).toBe('*.csv');
      expect(permissionSelect(wrapper).props('modelValue')).toBe(4);
      expect(parserSelect(wrapper).props('modelValue')).toBe(8);
    });

    it('falls back to an empty default model when no v-model is passed', () => {
      const wrapper = mount(IngestFormSftp, {
        props: { title: 'New', isLoading: false, backRoute: '/back' },
        global: globalOptions,
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('');
      expect(nativeValue(findInput(wrapper, 'Filename pattern'))).toBe('');
      expect(permissionSelect(wrapper).props('modelValue')).toBeNull();
      expect(parserSelect(wrapper).props('modelValue')).toBeNull();
      expect(parserSelect(wrapper).props('disable')).toBe(true);
    });
  });

  describe('prop changes', () => {
    it('updates title and back route', async () => {
      const { wrapper } = mountForm();

      await wrapper.setProps({ title: 'Other title', backRoute: '/other' } as Record<
        string,
        unknown
      >);

      expect(wrapper.find('h5').text()).toBe('Other title');
      expect(getBtn(wrapper, 'back').props('to')).toBe('/other');
    });

    it('passes isLoading to the Save button', async () => {
      const { wrapper } = mountForm();

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(false);

      await wrapper.setProps({ isLoading: true } as Record<string, unknown>);

      expect(getBtn(wrapper, 'Save').props('loading')).toBe(true);
    });

    it('passes itemPermissionGroup and itemParser to the selects', async () => {
      const group = { id: 1, name: 'Group1' } as unknown as PermissionGroup;
      const parser = { id: 2, name: 'Parser1' } as unknown as ParserRead;
      const { wrapper } = mountForm();

      expect(permissionSelect(wrapper).props('preselectedItem')).toBeUndefined();
      expect(parserSelect(wrapper).props('preselectedParser')).toBeUndefined();

      await wrapper.setProps({ itemPermissionGroup: group, itemParser: parser } as Record<
        string,
        unknown
      >);

      expect(permissionSelect(wrapper).props('preselectedItem')).toEqual(group);
      expect(parserSelect(wrapper).props('preselectedParser')).toEqual(parser);
    });
  });

  describe('permission group and parser', () => {
    it('passes the permission group id on to the parser select', () => {
      const { wrapper } = mountForm({ model: { permission_group_id: 4 } });

      expect(parserSelect(wrapper).props('permissionGroupId')).toBe(4);
    });

    it('writes the selected permission group and parser back to the model', async () => {
      const { wrapper, formData } = mountForm();

      permissionSelect(wrapper).vm.$emit('update:modelValue', 3);
      parserSelect(wrapper).vm.$emit('update:modelValue', 5);
      await flushPromises();

      expect(formData.permission_group_id).toBe(3);
      expect(formData.parser_id).toBe(5);
    });

    it('disables the parser select until a permission group is chosen', async () => {
      const { wrapper } = mountForm({ model: { permission_group_id: null } });

      expect(parserSelect(wrapper).props('disable')).toBe(true);

      permissionSelect(wrapper).vm.$emit('update:modelValue', 5);
      await flushPromises();

      expect(parserSelect(wrapper).props('disable')).toBe(false);
      expect(parserSelect(wrapper).props('permissionGroupId')).toBe(5);
    });

    it('applies the REQUIRED rule to both selects', () => {
      const { wrapper } = mountForm();

      expect(permissionSelect(wrapper).props('rules')).toEqual([rules.REQUIRED]);
      expect(parserSelect(wrapper).props('rules')).toEqual([rules.REQUIRED]);
    });
  });

  describe('v-model', () => {
    it('writes the text inputs back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Name'), 'New name');
      await typeInto(findInput(wrapper, 'Description'), 'New description');
      await typeInto(findInput(wrapper, 'Filename pattern'), '*.txt');

      expect(formData.name).toBe('New name');
      expect(formData.description).toBe('New description');
      expect(formData.filename_pattern).toBe('*.txt');
    });
  });

  describe('required fields and validation', () => {
    it('does not disable Save for an invalid form (validation happens on submit)', () => {
      const { wrapper } = mountForm({ model: { name: '', filename_pattern: '' } });

      expect(getBtn(wrapper, 'Save').props('disable')).toBe(false);
    });

    it('emits save exactly once for a valid form', async () => {
      const { wrapper } = mountForm();

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
      expect(wrapper.emitted('save')![0]).toEqual([]);
    });

    it.each([
      ['name has exactly 80 characters', { name: 'a'.repeat(80) }],
      ['description is empty', { description: null }],
    ])('emits save when %s', async (_label, model) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });

    it.each([
      ['name is empty', { name: '' }],
      ['name is null', { name: null }],
      ['name has more than 80 characters', { name: 'a'.repeat(81) }],
      ['filename pattern is empty', { filename_pattern: '' }],
      ['filename pattern is null', { filename_pattern: null }],
    ])('does not emit save when %s', async (_label, model) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toBeUndefined();
    });
  });
});
