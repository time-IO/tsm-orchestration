import { flushPromises, type VueWrapper } from '@vue/test-utils';
import { QBtn, QInput } from 'quasar';
import { defineComponent, h } from 'vue';

// QPage needs a QLayout as parent and renders nothing without one -> replace it with a div.
export const QPageStub = defineComponent({
  name: 'QPage',
  setup:
    (_, { slots }) =>
    () =>
      h('div', { class: 'q-page-stub' }, slots.default?.()),
});

// All QInputs whose label starts with the given text (labels contain hints like "(e.g. #)")
export const findInputs = (wrapper: VueWrapper, label: string) =>
  wrapper.findAllComponents(QInput).filter((i) => String(i.props('label')).startsWith(label));

// First matching QInput, throws a readable error instead of returning undefined
export const findInput = (wrapper: VueWrapper, label: string) => {
  const [first] = findInputs(wrapper, label);
  if (!first) throw new Error(`QInput with label "${label}" not found`);
  return first;
};

// Value of the native <input>/<textarea> inside a QInput, i.e. what the user sees (always a string)
export const nativeValue = (input: ReturnType<typeof findInput>) =>
  input.find<HTMLInputElement>('.q-field__native').element.value;

// Simulates typing into a QInput
export const typeInto = (input: ReturnType<typeof findInput>, value: string) =>
  input.find<HTMLInputElement>('.q-field__native').setValue(value);

// Returns undefined when missing -> use for "must not exist" assertions
export const findBtn = (wrapper: VueWrapper, label: string) =>
  wrapper.findAllComponents(QBtn).find((b) => b.props('label') === label);

// Throws when missing -> use for "must exist" interactions
export const getBtn = (wrapper: VueWrapper, label: string) => {
  const btn = findBtn(wrapper, label);
  if (!btn) throw new Error(`QBtn with label "${label}" not found`);
  return btn;
};

export const findBtnsByIcon = (wrapper: VueWrapper, icon: string) =>
  wrapper.findAllComponents(QBtn).filter((b) => b.props('icon') === icon);

// Submits the form and waits until the (async) QForm validation is done
export const submit = async (wrapper: VueWrapper) => {
  await wrapper.find('form').trigger('submit');
  await flushPromises();
};
