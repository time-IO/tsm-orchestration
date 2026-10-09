import {installQuasarPlugin} from "@quasar/quasar-app-extension-testing-unit-vitest";
import {mount} from '@vue/test-utils';
import{QBtn, QDialog} from 'quasar';
import {describe, expect, it} from 'vitest';

import HelpButton from "@/components/HelpButton.vue";

installQuasarPlugin();

const mountHelpButton = (
  props: {titleHelp?: string; textHelp?:string; termHelp?: string} = {},
) =>
  mount(HelpButton, {
    props,
    global: {
      stubs: {
        QDialog:{
          props:['modelValue'],
          emits: ['update:modelValue'],
          template: '<div v-if="modelValue" class="dialog"><slot/></div>',
        },
        QTooltip:{template: '<div class="tooltip"><slot/></div>'}
      },
    },
  })

const openDialog = async (wrapper: ReturnType<typeof mountHelpButton>) => {
  await wrapper.findComponent(QBtn).trigger('click');
};

describe('HelpButton', () => {
  it('keeps the dialog clossed initially', () =>{
    const wrapper = mountHelpButton({titleHelp: 'Title', textHelp: 'Text'});

    expect(wrapper.find('.dialog').exists()).toBe(false);
  });

  it('opens the dialog when the helpButton is clicked', async () => {
    const wrapper = mountHelpButton({titleHelp: 'Title', textHelp: 'Text'});

    await openDialog(wrapper);

    expect(wrapper.find('.dialog').exists()).toBe(true);
  });

  it('closes the dialog when the dialog emits update:modelValue false', async () => {
    const wrapper = mountHelpButton({titleHelp: 'Title', textHelp: 'Text'});
    await openDialog(wrapper);

    wrapper.findComponent(QDialog).vm.$emit('update:modelValue', false);
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.dialog').exists()).toBe(false);
  });

  it('shows titleHelp and textHelp in the dialog', async () =>{
    const wrapper = mountHelpButton({titleHelp: 'Some Help', textHelp: 'this helps'});
    await openDialog(wrapper);

    expect(wrapper.find('.text-h6').text()).toBe('Some Help');
    expect(wrapper.find('.dialog').text()).toContain('this helps');
  });

  it('updates the dialog content when the props change', async () => {
     const wrapper = mountHelpButton({ titleHelp: 'Old title', textHelp: 'Old text' });
     await openDialog(wrapper);

     await wrapper.setProps({titleHelp: 'New title', textHelp: 'New text'});

    expect(wrapper.find('.text-h6').text()).toBe('New title');
    expect(wrapper.find('.dialog').text()).toContain('New text');
  });

  it.for([
    {
      term: 'sync_interval',
      title: 'Sync Interval',
      text: 'Number of minutes between automatic synchronization runs',
    },
    {
      term: 'period',
      title: 'Period',
      text: 'Number of minutes to look back during each synchronization',
    },
  ])('shows the predefined text for termHelp $term', async (testCase) => {
    const wrapper = mountHelpButton({termHelp: testCase.term});

    await openDialog(wrapper);

    expect(wrapper.find('.text-h6').text()).toBe(testCase.title);
    expect(wrapper.find('.dialog').text()).toContain(testCase.text);
  });

  it('prefers termHelp over titleHelp and textHelp', async () => {
    const wrapper = mountHelpButton({
      termHelp: 'period',
      titleHelp: 'Custom title',
      textHelp: 'Custom text',
    });

    await openDialog(wrapper);

    expect(wrapper.find('.text-h6').text()).toBe('Period');
    expect(wrapper.find('.dialog').text()).not.toContain('Custom text');
  });

  it('falls back to title/textHelp for an unknown termHelp', async () => {
    const wrapper = mountHelpButton({
      termHelp: 'does_not_exist',
      titleHelp: 'Fallback title',
      textHelp: 'Fallback text',
    });

    await openDialog(wrapper);

    expect(wrapper.find('.text-h6').text()).toBe('Fallback title');
    expect(wrapper.find('.dialog').text()).toContain('Fallback text');
  });





















});
