import { flushPromises, mount } from '@vue/test-utils';
import { QIcon, QToggle, QField } from 'quasar';
import { describe, expect, it } from 'vitest';
import { defineComponent, h, reactive, type Component } from 'vue';

import {
  findInput,
  findInputs,
  getBtn,
  nativeValue,
  QPageStub,
  submit,
  typeInto,
} from './TestUtils';

type Model = Record<string, unknown>;

export type ModelFactory = (overrides?: Model) => Model;

export type MountOptions = {
  model?: Model;
  props?: Model;
  stubs?: Record<string, Component>;
};

export type SuiteOptions = {
  // Additional stubs, e.g. for a station select
  stubs?: Record<string, Component>;
  // false for forms whose sync interval is a read-only field instead of an input (e.g. TSystems)
  syncIntervalEditable?: boolean;
};

export const PermissionGroupSelectStub = defineComponent({
  name: 'PermissionGroupSelect',
  props: {
    modelValue: { type: null, default: null },
    preselectedItem: { type: null, default: null },
    rules: { type: Array, default: () => [] },
  },
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'permission-group-select-stub' }),
});

export const HelpButtonStub = defineComponent({
  name: 'HelpButton',
  props: { termHelp: { type: String, default: '' } },
  setup: () => () => h('span', { class: 'help-button-stub' }),
});

export const mountIngestForm = (
  component: Component,
  makeModel: ModelFactory,
  options: MountOptions = {},
) => {
  // reactive, because the component mutates the model object in place (v-model on formData.xyz)
  const formData = reactive(makeModel(options.model));
  const wrapper = mount(component, {
    props: {
      modelValue: formData,
      title: 'Test title',
      isLoading: false,
      backRoute: '/ingests',
      ...options.props,
    },
    global: {
      stubs: {
        QPage: QPageStub,
        PermissionGroupSelect: PermissionGroupSelectStub,
        HelpButton: HelpButtonStub,
        ...options.stubs,
      },
    },
  });
  return { wrapper, formData };
};

// Tests everything that all external API ingest forms have in common:
// title/back button, name, permission group, description, sync block, save button.
// Call inside a spec file after installQuasarPlugin().
export const describeExternalApiIngestForm = (
  component: Component,
  makeModel: ModelFactory,
  { stubs = {}, syncIntervalEditable = true }: SuiteOptions = {},
) => {
  const mountForm = (options: MountOptions = {}) =>
    mountIngestForm(component, makeModel, { ...options, stubs });

  describe('common external API ingest form', () => {
    describe('initialization', () => {
      it('shows the title and links the back button to backRoute', () => {
        const { wrapper } = mountForm({ props: { title: 'Create Ingest', backRoute: '/foo' } });

        expect(wrapper.find('h5').text()).toBe('Create Ingest');
        expect(getBtn(wrapper, 'back').props('to')).toBe('/foo');
      });

      it('shows the model values in the inputs', () => {
        const { wrapper, formData } = mountForm();

        expect(nativeValue(findInput(wrapper, 'Name'))).toBe(formData.name);
        if (syncIntervalEditable) {
          expect(nativeValue(findInput(wrapper, 'Sync Interval'))).toBe(
            String(formData.sync_interval_in_minutes),
          );
        }
      });

      it('passes the preselected permission group to the select', () => {
        const item = { id: 1, name: 'Group' };
        const { wrapper } = mountForm({ props: { itemPermissionGroup: item } });

        expect(wrapper.findComponent(PermissionGroupSelectStub).props('preselectedItem')).toEqual(
          item,
        );
      });

      it('connects the sync interval help button to its term', () => {
        const { wrapper } = mountForm();
        const terms = wrapper.findAllComponents(HelpButtonStub).map((b) => b.props('termHelp'));

        expect(terms).toContain('sync_interval');
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

      if (syncIntervalEditable) {
        // Guards the `.number` modifier: a string here breaks the backend (cf. flagUniLOF bug)
        it('writes the sync interval as a number, not a string', async () => {
          const { wrapper, formData } = mountForm();

          await typeInto(findInput(wrapper, 'Sync Interval'), '45');

          expect(formData.sync_interval_in_minutes).toBe(45);
        });
      }

      it('toggles sync_enabled with the toggle', async () => {
        const { wrapper, formData } = mountForm({ model: { sync_enabled: false } });

        await wrapper.findComponent(QToggle).trigger('click');
        expect(formData.sync_enabled).toBe(true);

        await wrapper.findComponent(QToggle).trigger('click');
        expect(formData.sync_enabled).toBe(false);
      });

      it('writes the selected permission group back to the model', async () => {
        const { wrapper, formData } = mountForm();

        wrapper.findComponent(PermissionGroupSelectStub).vm.$emit('update:modelValue', 5);
        await flushPromises();

        expect(formData.permission_group_id).toBe(5);
      });
    });

    describe('loading state', () => {
      it('passes isLoading to the Save button', async () => {
        const { wrapper } = mountForm();

        expect(getBtn(wrapper, 'Save').props('loading')).toBe(false);

        await wrapper.setProps({ isLoading: true } as Record<string, unknown>);

        expect(getBtn(wrapper, 'Save').props('loading')).toBe(true);
      });
    });

    describe('submit and validation', () => {
      const syncIntervalInvalidCases: Array<[string, Model]> = syncIntervalEditable
        ? [
            ['an empty sync interval', { sync_interval_in_minutes: null }],
            ['a non-integer sync interval', { sync_interval_in_minutes: 10.5 }],
            ['a sync interval below 10', { sync_interval_in_minutes: 9 }],
          ]
        : [];

      it('emits save exactly once for a valid form', async () => {
        const { wrapper } = mountForm();

        await submit(wrapper);

        expect(wrapper.emitted('save')).toHaveLength(1);
      });

      it.each([
        ['an empty name', { name: '' }],
        ['a name longer than 80 characters', { name: 'a'.repeat(81) }],
        ...syncIntervalInvalidCases,
      ] as Array<[string, Model]>)('does not emit save for %s', async (_, override) => {
        const { wrapper } = mountForm({ model: override });

        await submit(wrapper);

        expect(wrapper.emitted('save')).toBeUndefined();
      });

      if (syncIntervalEditable) {
        it('accepts the boundary value of 10 for the sync interval', async () => {
          const { wrapper } = mountForm({ model: { sync_interval_in_minutes: 10 } });

          await submit(wrapper);

          expect(wrapper.emitted('save')).toHaveLength(1);
        });
      }

      // The real PermissionGroupSelect is stubbed, so the form cannot enforce its rule.
      // Therefore the rule passed to it is verified directly.
      it('requires a permission group via the rule passed to the select', () => {
        const { wrapper } = mountForm();
        const [rule] = wrapper.findComponent(PermissionGroupSelectStub).props('rules') as Array<
          (val: unknown) => true | string
        >;

        expect(rule!(null)).not.toBe(true);
        expect(rule!(3)).toBe(true);
      });
    });
  });
};

// Tests the show/hide icon of a password-like QInput (label starts with the given text)
export const describePasswordToggle = (
  mountForm: (options?: MountOptions) => ReturnType<typeof mountIngestForm>,
  label: string,
) => {
  describe('password visibility', () => {
    it('masks the value by default and toggles it via the icon', async () => {
      const { wrapper } = mountForm();

      const getToggleIcon = () => {
        const icon = findInput(wrapper, label)
          .findAllComponents(QIcon)
          .find((i) => ['visibility', 'visibility_off'].includes(String(i.props('name'))));
        if (!icon) throw new Error('visibility icon not found');
        return icon;
      };
      const getType = () => findInput(wrapper, label).find('input').attributes('type');

      expect(getType()).toBe('password');
      expect(getToggleIcon().props('name')).toBe('visibility_off');

      await getToggleIcon().trigger('click');

      expect(getType()).toBe('text');
      expect(getToggleIcon().props('name')).toBe('visibility');

      await getToggleIcon().trigger('click');

      expect(getType()).toBe('password');
    });
  });
};

// Tests a read-only sync interval field (instead of an editable input)
export const describeFixedSyncInterval = (
  mountForm: (options?: MountOptions) => ReturnType<typeof mountIngestForm>,
) => {
  describe('fixed sync interval', () => {
    it('shows the sync interval from the model as read-only text', () => {
      const { wrapper } = mountForm({ model: { sync_interval_in_minutes: 60 } });
      const field = wrapper
        .findAllComponents(QField)
        .find((f) => String(f.props('label')).startsWith('Sync Interval'));

      expect(field).toBeDefined();
      expect(field!.props('readonly')).toBe(true);
      expect(field!.text()).toContain('60');
    });

    it('offers no editable sync interval input', () => {
      const { wrapper } = mountForm();

      expect(findInputs(wrapper, 'Sync Interval')).toHaveLength(0);
    });
  });
};
