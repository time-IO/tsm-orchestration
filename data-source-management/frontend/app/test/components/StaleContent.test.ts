import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, nextTick, ref } from 'vue';
import StaleContent from '@/components/common/StaleContent.vue';

// Mirrors ParserValidateBanner: a component whose root is another component (attributes fall through twice)
const Inner = defineComponent({
  props: { text: { type: String, required: true } },
  template: '<div class="inner">{{ text }}</div>',
});
const Outer = defineComponent({
  components: { Inner },
  props: { text: { type: String, required: true } },
  template: '<inner v-if="text" :text="text" />',
});

function mountWrapper() {
  const stale = ref(false);
  const text = ref('result');
  const wrapper = mount(
    defineComponent({
      components: { StaleContent, Outer },
      setup: () => ({ stale, text }),
      template: `
        <stale-content :stale="stale">
          <outer :text="text" />
          <div v-if="text" class="plain">{{ text }}</div>
        </stale-content>`,
    }),
  );
  return { wrapper, stale };
}

function opacities(wrapper: ReturnType<typeof mount>) {
  return ['.inner', '.plain'].map(
    (selector) => (wrapper.find(selector).element as HTMLElement).style.opacity,
  );
}

describe('StaleContent', () => {
  it('renders no element of its own', () => {
    const { wrapper } = mountWrapper();
    const inner = wrapper.find('.inner').element;
    expect(inner.nextElementSibling?.classList.contains('plain')).toBe(true);
  });

  it('fades all children while stale and restores them afterwards', async () => {
    const { wrapper, stale } = mountWrapper();
    expect(opacities(wrapper)).toEqual(['', '']);

    stale.value = true;
    await nextTick();
    expect(opacities(wrapper)).toEqual(['0.4', '0.4']);

    stale.value = false;
    await nextTick();
    expect(opacities(wrapper)).toEqual(['', '']);
  });
});
