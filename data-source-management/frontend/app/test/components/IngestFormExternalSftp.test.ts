import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { QBtnToggle, QIcon, QToggle } from 'quasar';
import { describe, expect, it } from 'vitest';
import { defineComponent, h, reactive } from 'vue';

import IngestFormExternalSftp from '@/components/IngestFormExternalSftp.vue';
import type { IngestExternalSftpCreate } from '@/services/ingest_external_sftp/types';
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

const makeFormData = (
  overrides: Partial<IngestExternalSftpCreate> = {},
): IngestExternalSftpCreate => ({
  permission_group_id: 1,
  name: 'My ingest',
  description: null,
  parser_id: 2,
  filename_pattern: '*.csv',
  uri: 'sftp://ftp.example.org',
  path: '/data',
  password: 'secret',
  username: 'user',
  sync_enabled: false,
  sync_interval_in_minutes: 10,
  ...overrides,
});

type MountOptions = {
  model?: Partial<IngestExternalSftpCreate>;
  props?: Record<string, unknown>;
};

// The model is reactive so that the component's v-model mutations (formData.value.x = ...)
// are visible in the test and also trigger a re-render.
const mountForm = ({ model = {}, props = {} }: MountOptions = {}) => {
  const formData = reactive(makeFormData(model));
  const wrapper = mount(IngestFormExternalSftp, {
    props: {
      title: 'New ingest',
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
const protocolToggle = (w: VueWrapper) => w.findComponent(QBtnToggle);
const uriInput = (w: VueWrapper) => findInput(w, 'Fileserver URI');
const passwordIcon = (w: VueWrapper, name: string) =>
  w.findAllComponents(QIcon).find((i) => i.props('name') === name);

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('IngestFormExternalSftp', () => {
  describe('initialization', () => {
    it('shows the title and passes backRoute to the back button', () => {
      const { wrapper } = mountForm({ props: { title: 'Copy ingest', backRoute: '/ingest/7' } });

      expect(wrapper.find('h5').text()).toBe('Copy ingest');
      expect(getBtn(wrapper, 'back').props('to')).toBe('/ingest/7');
    });

    it('shows the model values in the inputs', () => {
      const { wrapper } = mountForm({ model: { description: 'Some text' } });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('My ingest');
      expect(nativeValue(findInput(wrapper, 'Description'))).toBe('Some text');
      expect(nativeValue(findInput(wrapper, 'Filename pattern'))).toBe('*.csv');
      expect(nativeValue(findInput(wrapper, 'Path'))).toBe('/data');
      expect(nativeValue(findInput(wrapper, 'Username'))).toBe('user');
      expect(nativeValue(findInput(wrapper, 'Password'))).toBe('secret');
      expect(nativeValue(findInput(wrapper, 'Sync Interval'))).toBe('10');
    });

    it('shows the sync toggle according to the model', () => {
      const { wrapper } = mountForm({ model: { sync_enabled: true } });

      expect(wrapper.findComponent(QToggle).props('modelValue')).toBe(true);
    });

    it('falls back to an empty default model when no v-model is passed', () => {
      const wrapper = mount(IngestFormExternalSftp, {
        props: { title: 'New', isLoading: false, backRoute: '/back' },
        global: globalOptions,
      });

      expect(nativeValue(findInput(wrapper, 'Name'))).toBe('');
      expect(nativeValue(uriInput(wrapper))).toBe('');
      expect(wrapper.findComponent(QToggle).props('modelValue')).toBe(false);
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
    it('passes the model values to the selects', () => {
      const { wrapper } = mountForm({ model: { permission_group_id: 4, parser_id: 8 } });

      expect(permissionSelect(wrapper).props('modelValue')).toBe(4);
      expect(parserSelect(wrapper).props('modelValue')).toBe(8);
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

  describe('server URI and protocol', () => {
    it('offers SFTP and FTP in the protocol toggle', () => {
      const { wrapper } = mountForm();

      expect(protocolToggle(wrapper).props('options')).toEqual([
        { label: 'SFTP', value: 'sftp' },
        { label: 'FTP', value: 'ftp' },
      ]);
    });

    it.each([
      ['sftp://host.org', 'host.org', 'sftp'],
      ['ftp://host.org', 'host.org', 'ftp'],
      ['sftp://host.org:2222/', 'host.org:2222', 'sftp'],
      ['host.org', 'host.org', 'sftp'],
    ])(
      'shows the uri "%s" as host "%s" with protocol "%s"',
      (uri, expectedHost, expectedProtocol) => {
        const { wrapper } = mountForm({ model: { uri } });

        expect(nativeValue(uriInput(wrapper))).toBe(expectedHost);
        expect(protocolToggle(wrapper).props('modelValue')).toBe(expectedProtocol);
        expect(uriInput(wrapper).props('prefix')).toBe(`${expectedProtocol}://`);
      },
    );

    it('defaults to sftp for an empty uri', () => {
      const { wrapper } = mountForm({ model: { uri: null } });

      expect(nativeValue(uriInput(wrapper))).toBe('');
      expect(protocolToggle(wrapper).props('modelValue')).toBe('sftp');
      expect(uriInput(wrapper).props('prefix')).toBe('sftp://');
    });

    it.each([
      ['example.org', 'sftp://example.org'],
      ['example.org:2222', 'sftp://example.org:2222'],
      ['sftp://example.org/', 'sftp://example.org'],
      ['ftp://example.org', 'ftp://example.org'],
    ])('stores the typed host "%s" as uri "%s"', async (typed, expectedUri) => {
      const { wrapper, formData } = mountForm({ model: { uri: null } });

      await typeInto(uriInput(wrapper), typed);

      expect(formData.uri).toBe(expectedUri);
    });

    it('switches the protocol when the typed host starts with a protocol prefix', async () => {
      const { wrapper } = mountForm({ model: { uri: null } });

      await typeInto(uriInput(wrapper), 'ftp://example.org');

      expect(protocolToggle(wrapper).props('modelValue')).toBe('ftp');
      expect(uriInput(wrapper).props('prefix')).toBe('ftp://');
      expect(nativeValue(uriInput(wrapper))).toBe('example.org');
    });

    it('keeps the current protocol when a host without prefix is typed', async () => {
      const { wrapper, formData } = mountForm({ model: { uri: 'ftp://old.org' } });

      await typeInto(uriInput(wrapper), 'new.org');

      expect(formData.uri).toBe('ftp://new.org');
    });

    it('sets the uri to null when the host is cleared', async () => {
      const { wrapper, formData } = mountForm({ model: { uri: 'sftp://example.org' } });

      await typeInto(uriInput(wrapper), '');

      expect(formData.uri).toBeNull();
    });

    it('rewrites the uri with the new protocol when the toggle changes', async () => {
      const { wrapper, formData } = mountForm({ model: { uri: 'sftp://example.org:22' } });

      protocolToggle(wrapper).vm.$emit('update:modelValue', 'ftp');
      await flushPromises();

      expect(formData.uri).toBe('ftp://example.org:22');
      expect(uriInput(wrapper).props('prefix')).toBe('ftp://');
    });

    it('keeps the uri null when the toggle changes while no host is entered', async () => {
      const { wrapper, formData } = mountForm({ model: { uri: null } });

      protocolToggle(wrapper).vm.$emit('update:modelValue', 'ftp');
      await flushPromises();

      expect(formData.uri).toBeNull();
      expect(uriInput(wrapper).props('prefix')).toBe('ftp://');
    });

    it('follows the protocol when the uri is changed from outside', async () => {
      const { wrapper, formData } = mountForm({ model: { uri: 'sftp://example.org' } });

      formData.uri = 'ftp://other.org';
      await flushPromises();

      expect(protocolToggle(wrapper).props('modelValue')).toBe('ftp');
      expect(nativeValue(uriInput(wrapper))).toBe('other.org');
    });
  });

  describe('password visibility', () => {
    it('hides the password initially', () => {
      const { wrapper } = mountForm();

      expect(findInput(wrapper, 'Password').props('type')).toBe('password');
      expect(passwordIcon(wrapper, 'visibility_off')).toBeDefined();
      expect(passwordIcon(wrapper, 'visibility')).toBeUndefined();
    });

    it('toggles between hidden and visible with the icon', async () => {
      const { wrapper } = mountForm();

      await passwordIcon(wrapper, 'visibility_off')!.trigger('click');

      expect(findInput(wrapper, 'Password').props('type')).toBe('text');
      expect(passwordIcon(wrapper, 'visibility')).toBeDefined();

      await passwordIcon(wrapper, 'visibility')!.trigger('click');

      expect(findInput(wrapper, 'Password').props('type')).toBe('password');
    });
  });

  describe('v-model', () => {
    it('writes the text inputs back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Name'), 'New name');
      await typeInto(findInput(wrapper, 'Description'), 'New description');
      await typeInto(findInput(wrapper, 'Filename pattern'), '*.txt');
      await typeInto(findInput(wrapper, 'Path'), '/other');
      await typeInto(findInput(wrapper, 'Username'), 'other-user');
      await typeInto(findInput(wrapper, 'Password'), 'other-secret');

      expect(formData.name).toBe('New name');
      expect(formData.description).toBe('New description');
      expect(formData.filename_pattern).toBe('*.txt');
      expect(formData.path).toBe('/other');
      expect(formData.username).toBe('other-user');
      expect(formData.password).toBe('other-secret');
    });

    it('toggles sync_enabled on and off with the toggle', async () => {
      const { wrapper, formData } = mountForm({ model: { sync_enabled: false } });

      await wrapper.findComponent(QToggle).trigger('click');
      expect(formData.sync_enabled).toBe(true);

      await wrapper.findComponent(QToggle).trigger('click');
      expect(formData.sync_enabled).toBe(false);
    });

    it('writes the sync interval back to the model as a number', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Sync Interval'), '15');

      expect(formData.sync_interval_in_minutes).toBe(15);
    });
  });

  describe('required fields and validation', () => {
    it('does not disable Save for an invalid form (validation happens on submit)', () => {
      const { wrapper } = mountForm({ model: { name: '', path: '' } });

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
      ['sync interval is exactly 10', { sync_interval_in_minutes: 10 }],
      ['sync is enabled', { sync_enabled: true }],
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
      ['uri is missing', { uri: null }],
      ['path is empty', { path: '' }],
      ['username is empty', { username: '' }],
      ['password is empty', { password: '' }],
      ['sync interval is missing', { sync_interval_in_minutes: null }],
      ['sync interval is below 10', { sync_interval_in_minutes: 9 }],
      ['sync interval is not an integer', { sync_interval_in_minutes: 10.5 }],
    ])('does not emit save when %s', async (_label, model) => {
      const { wrapper } = mountForm({ model });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toBeUndefined();
    });
  });
});
