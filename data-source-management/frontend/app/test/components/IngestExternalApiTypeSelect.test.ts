import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { QSelect } from 'quasar';
import IngestExternalApiTypeSelect from '@/components/IngestExternalApiTypeSelect.vue';

installQuasarPlugin();

const API_TYPES = [
  { id: 'bosch', name: 'Bosch IoT' },
  { id: 'dwd', name: 'Deutscher Wetterdienst' },
  { id: 'nm', name: 'Neutron Monitor' },
  { id: 'ttn', name: 'The Things network' },
  { id: 'tsystems', name: 'TSystems' },
  { id: 'uba', name: 'Umweltbundesamt (UBA) Air Data' },
  { id: 'sensoto', name: 'Sensoto' },
];

function mountIngestExternalApiTypeSelect(props: Record<string, unknown> = {}) {
  const wrapper = mount(IngestExternalApiTypeSelect, {
    props: {
      modelValue: null,
      // echo the emitted value back, like a real parent using v-model would
      'onUpdate:modelValue': (v: unknown) => wrapper.setProps({ modelValue: v }),
      ...props,
    },
  });
  return wrapper;
}

const getSelect = (w: ReturnType<typeof mountIngestExternalApiTypeSelect>) =>
  w.findComponent(QSelect);

describe('IngestExternalApiTypeSelect', () => {
  describe('initialization', () => {
    it('offers exactly the seven api types in this order', () => {
      const options = getSelect(mountIngestExternalApiTypeSelect()).props('options');
      expect(options).toEqual(API_TYPES);
    });

    it('configures QSelect for id/name options with emit-value, map-options and clearable', () => {
      const select = getSelect(mountIngestExternalApiTypeSelect());
      expect(select.props('optionValue')).toBe('id');
      expect(select.props('optionLabel')).toBe('name');
      expect(select.props('emitValue')).toBe(true);
      expect(select.props('clearable')).toBe(true);
    });

    it('shows label and hint', () => {
      const select = getSelect(mountIngestExternalApiTypeSelect());
      expect(select.props('label')).toBe('API type');
      expect(select.props('hint')).toBe('Select the API type');
    });

    it('shows no selection when modelValue is null', () => {
      const w = mountIngestExternalApiTypeSelect({ modelValue: null });
      expect(w.find('.q-field__native').text()).toBe('');
    });

    it('shows no selection when modelValue is undefined', () => {
      // the filter component uses undefined as its "no filter" value
      const w = mountIngestExternalApiTypeSelect({ modelValue: undefined });
      expect(w.find('.q-field__native').text()).toBe('');
    });

    it.each(API_TYPES.map((t) => [t.id, t.name]))(
      'displays the short id for modelValue "%s"',
      (id, name) => {
        const w = mountIngestExternalApiTypeSelect({ modelValue: id });
        expect(w.find('.q-field__native').text()).toBe(id);
      },
    );
  });

  describe('prop changes', () => {
    it('updates the display when modelValue changes from outside', async () => {
      const w = mountIngestExternalApiTypeSelect({ modelValue: 'bosch' });
      expect(w.find('.q-field__native').text()).toBe('bosch');

      await w.setProps({ modelValue: 'uba' });

      expect(getSelect(w).props('modelValue')).toBe('uba');
      expect(w.find('.q-field__native').text()).toBe('uba');
    });

    it('clears the display when modelValue is reset to undefined from outside', async () => {
      const w = mountIngestExternalApiTypeSelect({ modelValue: 'sensoto' });
      await w.setProps({ modelValue: undefined });
      expect(w.find('.q-field__native').text()).toBe('');
    });
  });

  describe('v-model', () => {
    it('emits update:modelValue with the id (not the label)', async () => {
      const w = mountIngestExternalApiTypeSelect();
      await getSelect(w).vm.$emit('update:modelValue', 'ttn');

      expect(w.emitted('update:modelValue')).toEqual([['ttn']]);
    });

    it('emits null when the selection is cleared', async () => {
      const w = mountIngestExternalApiTypeSelect({ modelValue: 'dwd' });
      await getSelect(w).vm.$emit('update:modelValue', null);

      expect(w.emitted('update:modelValue')?.at(-1)).toEqual([null]);
    });
  });

  describe('attribute passthrough ($attrs)', () => {
    it('forwards dense to QSelect', () => {
      // the filter component passes dense to this select
      const w = mountIngestExternalApiTypeSelect({ dense: true });
      expect(getSelect(w).props('dense')).toBe(true);
    });
  });
});
