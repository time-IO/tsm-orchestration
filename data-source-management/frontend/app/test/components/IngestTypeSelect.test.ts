import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { QSelect } from 'quasar';
import IngestTypeSelect from '@/components/IngestTypeSelect.vue';

installQuasarPlugin();

const INGEST_TYPES = [
  { id: 'mqtt', name: 'Mqtt' },
  { id: 'sftp', name: 'Sftp' },
  { id: 'external_api', name: 'External Api' },
  { id: 'external_sftp', name: 'External Ftp/Sftp' },
  { id: 'external_mqtt', name: 'External Mqtt' },
  { id: 'http', name: 'Http' },
];

function mountIngestTypeSelect(props: Record<string, unknown> = {}) {
  const wrapper = mount(IngestTypeSelect, {
    props: {
      modelValue: null,
      // echo the emitted value back, like a real parent using v-model would
      'onUpdate:modelValue': (v: unknown) => wrapper.setProps({ modelValue: v }),
      ...props,
    },
  });
  return wrapper;
}

const getSelect = (w: ReturnType<typeof mountIngestTypeSelect>) => w.findComponent(QSelect);

describe('IngestTypeSelect', () => {
  describe('initialization', () => {
    it('offers exactly the six ingest types in this order', () => {
      const options = getSelect(mountIngestTypeSelect()).props('options');
      expect(options).toEqual(INGEST_TYPES);
    });

    it('configures QSelect for id/name options with emit-value and clearable', () => {
      const select = getSelect(mountIngestTypeSelect());
      expect(select.props('optionValue')).toBe('id');
      expect(select.props('optionLabel')).toBe('name');
      expect(select.props('emitValue')).toBe(true);
      expect(select.props('clearable')).toBe(true);
    });

    it('shows label and hint', () => {
      const select = getSelect(mountIngestTypeSelect());
      expect(select.props('label')).toBe('Ingest type');
      expect(select.props('hint')).toBe('Select the Ingest type');
    });

    it('shows no selection when modelValue is null', () => {
      const w = mountIngestTypeSelect({ modelValue: null });
      expect(w.find('.q-field__native').text()).toBe('');
    });

    it('shows no selection when modelValue is undefined', () => {
      // the filter component uses undefined as its "no filter" value
      const w = mountIngestTypeSelect({ modelValue: undefined });
      expect(w.find('.q-field__native').text()).toBe('');
    });

    it.each(INGEST_TYPES.map((t) => [t.id, t.name]))(
      'displays the label (not the id) for modelValue "%s"',
      (id, name) => {
        const w = mountIngestTypeSelect({ modelValue: id });
        expect(w.find('.q-field__native').text()).toBe(name);
      },
    );
  });

  describe('prop changes', () => {
    it('updates the display when modelValue changes from outside', async () => {
      const w = mountIngestTypeSelect({ modelValue: 'mqtt' });
      expect(w.find('.q-field__native').text()).toBe('Mqtt');

      await w.setProps({ modelValue: 'external_sftp' });

      expect(getSelect(w).props('modelValue')).toBe('external_sftp');
      expect(w.find('.q-field__native').text()).toBe('External Ftp/Sftp');
    });

    it('clears the display when modelValue is reset to undefined from outside', async () => {
      const w = mountIngestTypeSelect({ modelValue: 'http' });
      await w.setProps({ modelValue: undefined });
      expect(w.find('.q-field__native').text()).toBe('');
    });
  });

  describe('v-model', () => {
    it('emits update:modelValue with the id (not the label)', async () => {
      const w = mountIngestTypeSelect();
      await getSelect(w).vm.$emit('update:modelValue', 'external_api');

      expect(w.emitted('update:modelValue')).toEqual([['external_api']]);
    });

    it('emits null when the selection is cleared', async () => {
      const w = mountIngestTypeSelect({ modelValue: 'sftp' });
      await getSelect(w).vm.$emit('update:modelValue', null);

      expect(w.emitted('update:modelValue')?.at(-1)).toEqual([null]);
    });
  });

  describe('attribute passthrough ($attrs)', () => {
    it('forwards dense to QSelect', () => {
      // the filter component passes dense to this select
      const w = mountIngestTypeSelect({ dense: true });
      expect(getSelect(w).props('dense')).toBe(true);
    });
  });
});
