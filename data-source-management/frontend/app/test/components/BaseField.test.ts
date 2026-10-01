import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import BaseField from '@/components/common/BaseField.vue';

installQuasarPlugin();

describe('BaseField', () => {
  it('emits a click when enabled', async () => {
    const wrapper = mount(BaseField, {
      props: { disable: false },
    });

    await wrapper.trigger('click');

    expect(wrapper.emitted('click')).toHaveLength(1);
  });

  it('does not emit a click when disabled', async () => {
    const wrapper = mount(BaseField, {
      props: { disable: true },
    });

    await wrapper.trigger('click');

    expect(wrapper.emitted('click')).toBeUndefined();
  });
});
