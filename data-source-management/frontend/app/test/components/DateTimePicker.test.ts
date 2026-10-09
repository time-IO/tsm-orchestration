import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { mount } from '@vue/test-utils';
import { QDate, QTime } from 'quasar';
import { describe, expect, it } from 'vitest';
import type { Component } from 'vue';

import DateTimePicker from '@/components/DateTimePicker.vue';

installQuasarPlugin();

const DATE = '2024-01-02 03:04:05';

const mountPicker = (props: { modelValue?: string } = {}, attrs: Record<string, unknown> = {}) =>
  mount(DateTimePicker, {
    props,
    attrs,
    global: {
      stubs: { QPopupProxy: { template: '<div class="popup"><slot /></div>' } },
    },
  });

describe('DateTimePicker', () => {
  it('shows the modulValue in the input', () => {
    const wrapper = mountPicker({ modelValue: DATE });

    expect(wrapper.find('input').element.value).toBe(DATE);
  });

  it('updates the inpur when the modelValue-prop changes', async () => {
    const wrapper = mountPicker({ modelValue: DATE });

    await wrapper.setProps({ modelValue: '2025-12-31 23:59:59' });

    expect(wrapper.find('input').element.value).toBe('2025-12-31 23:59:59');
  });

  it('emits update:modelValue when the user types a value', async () => {
    const wrapper = mountPicker();

    await wrapper.find('input').setValue(DATE);

    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([DATE]);
  });

  it('passes the modelValue to the date and time pickers', () => {
    const wrapper = mountPicker({ modelValue: DATE });

    expect(wrapper.findComponent(QDate).props('modelValue')).toBe(DATE);
    expect(wrapper.findComponent(QTime).props('modelValue')).toBe(DATE);
  });

  it.for<{ name: string; component: Component }>([
    { name: 'QDate', component: QDate },
    { name: 'QTime', component: QTime },
  ])('emits update:modelValue when $name changes', ({ component }) => {
    const wrapper = mountPicker();

    wrapper.findComponent(component).vm.$emit('update:modelValue', DATE);

    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([DATE]);
  });
});
