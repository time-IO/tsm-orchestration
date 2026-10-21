import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { defineComponent, h, reactive } from 'vue';

import IngestFormMqtt from '@/components/IngestFormMqtt.vue';
import type { IngestMqttCreate, IngestMqttUpdate } from '@/services/ingest_mqtt/types';
import type { PermissionGroup } from '@/services/permission_group/types';
import { rules } from '@/utils/validation/rules';
import {
  findInput,
  findInputs,
  getBtn,
  nativeValue,
  QPageStub,
  submit,
  typeInto,
} from './utils/TestUtils';

installQuasarPlugin();

// Same shape as the model in IngestFormMqtt.vue; username only exists on some variants.
type MqttFormData = (IngestMqttCreate | IngestMqttUpdate) & { username?: string | null };

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

const PermissionGroupSelectStub = defineComponent({
  name: 'PermissionGroupSelect',
  props: ['modelValue', 'preselectedItem', 'rules'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'permission-group-select-stub' }),
});

const MqttParserSelectStub = defineComponent({
  name: 'MqttParserSelect',
  props: ['modelValue', 'preselectedItemId'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'mqtt-parser-select-stub' }),
});

const globalOptions = {
  stubs: {
    QPage: QPageStub,
    PermissionGroupSelect: PermissionGroupSelectStub,
    MqttParserSelect: MqttParserSelectStub,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// No username key by default, like the component's own default model.
// Tests that need a username pass `username` explicitly.
const makeFormData = (overrides: Partial<MqttFormData> = {}): MqttFormData => ({
  name: 'My ingest',
  permission_group_id: 1,
  description: null,
  parser_id: 2,
  ...overrides,
});

type MountOptions = {
  model?: Partial<MqttFormData>;
  props?: Record<string, unknown>;
};

// The model is reactive so that the component's v-model mutations (formData.value.x = ...)
// are visible in the test and also trigger a re-render.
const mountForm = ({ model = {}, props = {} }: MountOptions = {}) => {
  const formData = reactive(makeFormData(model));
  const wrapper = mount(IngestFormMqtt, {
    props: {
      title: 'New MQTT ingest',
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
const parserSelect = (w: VueWrapper) => w.findComponent(MqttParserSelectStub);
const usernameInputs = (w: VueWrapper) => findInputs(w, 'MQTT Username');

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('IngestFormMqtt', () => {
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
      expect(permissionSelect(wrapper).props('modelValue')).toBe(4);
      expect(parserSelect(wrapper).props('modelValue')).toBe(8);
    });

    it('falls back to an empty default model when no v-model is passed', () => {
      const wrapper = mount(IngestFormMqtt, {
        props: { title: 'New', isLoading: false, backRoute: '/back' },
        global: globalOptions,
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('');
      expect(nativeValue(findInput(wrapper, 'Description'))).toBe('');
      expect(permissionSelect(wrapper).props('modelValue')).toBeNull();
      expect(parserSelect(wrapper).props('modelValue')).toBeNull();
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

    it('passes itemPermissionGroup to the permission group select', async () => {
      const group = { id: 1, name: 'Group1' } as unknown as PermissionGroup;
      const { wrapper } = mountForm();

      expect(permissionSelect(wrapper).props('preselectedItem')).toBeUndefined();

      await wrapper.setProps({ itemPermissionGroup: group } as Record<string, unknown>);

      expect(permissionSelect(wrapper).props('preselectedItem')).toEqual(group);
    });

    it('passes itemParserId to the parser select', async () => {
      const { wrapper } = mountForm();

      expect(parserSelect(wrapper).props('preselectedItemId')).toBeUndefined();

      await wrapper.setProps({ itemParserId: 12 } as Record<string, unknown>);

      expect(parserSelect(wrapper).props('preselectedItemId')).toBe(12);
    });

    it('shows the username input only while allowUsernameInput is true', async () => {
      const { wrapper } = mountForm({ model: { username: null } });

      expect(usernameInputs(wrapper)).toHaveLength(0);

      await wrapper.setProps({ allowUsernameInput: true } as Record<string, unknown>);
      expect(usernameInputs(wrapper)).toHaveLength(1);

      await wrapper.setProps({ allowUsernameInput: false } as Record<string, unknown>);
      expect(usernameInputs(wrapper)).toHaveLength(0);
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

    it('writes the selected permission group and parser back to the model', async () => {
      const { wrapper, formData } = mountForm();

      permissionSelect(wrapper).vm.$emit('update:modelValue', 3);
      parserSelect(wrapper).vm.$emit('update:modelValue', 5);
      await flushPromises();

      expect(formData.permission_group_id).toBe(3);
      expect(formData.parser_id).toBe(5);
    });

    it('applies the REQUIRED rule to the permission group select', () => {
      const { wrapper } = mountForm();

      expect(permissionSelect(wrapper).props('rules')).toEqual([rules.REQUIRED]);
    });
  });

  describe('username', () => {
    it('shows the username from the model', () => {
      const { wrapper } = mountForm({
        model: { username: 'my-user-01' },
        props: { allowUsernameInput: true },
      });

      expect(nativeValue(findInput(wrapper, 'MQTT Username'))).toBe('my-user-01');
    });

    it('shows an empty input when the username is null', () => {
      const { wrapper } = mountForm({
        model: { username: null },
        props: { allowUsernameInput: true },
      });

      expect(nativeValue(findInput(wrapper, 'MQTT Username'))).toBe('');
    });

    it('writes the typed username back to the model', async () => {
      const { wrapper, formData } = mountForm({
        model: { username: null },
        props: { allowUsernameInput: true },
      });

      await typeInto(findInput(wrapper, 'MQTT Username'), 'my-user-01');

      expect(formData.username).toBe('my-user-01');
    });

    it('does not add a username to a model that has no username field', async () => {
      // the setter only writes when the model already has a username key
      const { wrapper, formData } = mountForm({ props: { allowUsernameInput: true } });

      await typeInto(findInput(wrapper, 'MQTT Username'), 'my-user-01');

      expect('username' in formData).toBe(false);
      expect(findInput(wrapper, 'MQTT Username').props('modelValue')).toBeNull();
    });
  });

  describe('required fields and validation', () => {
    it('does not disable Save for an invalid form (validation happens on submit)', () => {
      const { wrapper } = mountForm({ model: { name: '' } });

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
      ['parser is not set', { parser_id: null }],
    ])('emits save when %s', async (_label, model) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });

    it.each([
      ['name is empty', { name: '' }],
      ['name is null', { name: null }],
      ['name has more than 80 characters', { name: 'a'.repeat(81) }],
    ])('does not emit save when %s', async (_label, model) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toBeUndefined();
    });

    describe('username (only validated while the input is shown)', () => {
      it.each([
        ['no username is entered (null)', { username: null }],
        ['the username was cleared (empty string)', { username: '' }],
        ['the username has exactly 8 characters', { username: 'abcdefg1' }],
        ['the username contains digits and hyphens', { username: 'my-user-01' }],
      ])('emits save when %s', async (_label, model) => {
        const { wrapper } = mountForm({ model, props: { allowUsernameInput: true } });

        await submit(wrapper);

        expect(wrapper.emitted('save')).toHaveLength(1);
      });

      it.each([
        ['the username has 7 characters', { username: 'abcdef1' }],
        ['the username contains uppercase letters', { username: 'Abcdefg12' }],
        ['the username contains an underscore', { username: 'abcdefg_1' }],
        ['the username contains whitespace', { username: 'abcd efgh' }],
      ])('does not emit save when %s', async (_label, model) => {
        const { wrapper } = mountForm({ model, props: { allowUsernameInput: true } });

        await submit(wrapper);

        expect(wrapper.emitted('save')).toBeUndefined();
      });

      it('ignores an invalid username while the input is hidden', async () => {
        const { wrapper } = mountForm({
          model: { username: 'abc' },
          props: { allowUsernameInput: false },
        });

        await submit(wrapper);

        expect(wrapper.emitted('save')).toHaveLength(1);
      });
    });
  });
});
