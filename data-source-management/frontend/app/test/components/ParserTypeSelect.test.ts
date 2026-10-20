import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { QSelect } from 'quasar';
import ParserTypeSelect from '@/components/ParserTypeSelect.vue';

installQuasarPlugin();

function mountParsertypeSelect(props: Record<string, unknown> = {}) {
  const wrapper = mount(ParserTypeSelect, {
    props: {
      modelValue: null,
      // echo the emitted value back, like a real parent using v-model would
      'onUpdate:modelValue': (v: unknown) => wrapper.setProps({ modelValue: v }),
      ...props,
    },
  });
  return wrapper;
}

const getSelect = (w: ReturnType<typeof mountParsertypeSelect>) => w.findComponent(QSelect);

describe('ParserTypeSelect', () => {
  describe('initialization', () => {
    it('offers exactly the types csv, json and soilcan', () => {
      const options = getSelect(mountParsertypeSelect()).props('options') as {
        id: string;
        name: string;
      }[];
      expect(options).toEqual([
        { id: 'csv', name: 'CSV' },
        { id: 'json', name: 'JSON' },
        { id: 'soilcan', name: 'SOILCAN' },
      ]);
    });

    it('configures QSelect for id/name options with emit-value and clearable', () => {
      const select = getSelect(mountParsertypeSelect());
      expect(select.props('optionValue')).toBe('id');
      expect(select.props('optionLabel')).toBe('name');
      expect(select.props('emitValue')).toBe(true);
      expect(select.props('clearable')).toBe(true);
    });

    it('shows label and hint', () => {
      const select = getSelect(mountParsertypeSelect());
      expect(select.props('label')).toBe('Parser type');
      expect(select.props('hint')).toBe('Select the parser type');
    });

    it('shows no selection when modelValue is null', () => {
      const w = mountParsertypeSelect({ modelValue: null });
      expect(w.find('.q-field__native').text()).toBe('');
    });

    it('displays the option label (not the id) for a preset modelValue', () => {
      const w = mountParsertypeSelect({ modelValue: 'soilcan' });
      expect(getSelect(w).props('modelValue')).toBe('soilcan');
      expect(w.find('.q-field__native').text()).toContain('SOILCAN');
    });
  });

  describe('prop changes', () => {
    it('updates the display when modelValue changes from outside', async () => {
      const w = mountParsertypeSelect({ modelValue: 'csv' });
      expect(w.find('.q-field__native').text()).toContain('CSV');

      await w.setProps({ modelValue: 'json' });

      expect(getSelect(w).props('modelValue')).toBe('json');
      expect(w.find('.q-field__native').text()).toContain('JSON');
    });

    it('clears the display when modelValue is set to null from outside', async () => {
      const w = mountParsertypeSelect({ modelValue: 'csv' });
      await w.setProps({ modelValue: null });
      expect(w.find('.q-field__native').text()).toBe('');
    });
  });

  describe('v-model', () => {
    it('emits update:modelValue with the id (not the label)', async () => {
      const w = mountParsertypeSelect();
      await getSelect(w).vm.$emit('update:modelValue', 'json');

      expect(w.emitted('update:modelValue')).toEqual([['json']]);
    });

    it('emits null when the selection is cleared', async () => {
      const w = mountParsertypeSelect({ modelValue: 'csv' });
      await getSelect(w).vm.$emit('update:modelValue', null);

      expect(w.emitted('update:modelValue')?.at(-1)).toEqual([null]);
    });
  });

  describe('attribute passthrough ($attrs)', () => {
    it('forwards disable to QSelect', () => {
      const w = mountParsertypeSelect({ disable: true });
      expect(getSelect(w).props('disable')).toBe(true);
    });
  });
});
