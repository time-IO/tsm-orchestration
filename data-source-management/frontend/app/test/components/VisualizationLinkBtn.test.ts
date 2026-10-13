import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import VisualizationLinkBtn from '@/components/VisualizationLinkBtn.vue'; // adjust path

installQuasarPlugin();

const mountBtn = (uuid?: string | null) =>
  mount(VisualizationLinkBtn, { props: uuid === undefined ? {} : { uuid } });

describe('VisualizationBtn', () => {
  it.for([undefined, null, ''])('renders no link when uuid is %j', (uuid) => {
    const wrapper = mountBtn();

    expect(wrapper.find('a').exists()).toBe(false); //<a> for link (q-btn with href renders <a>)
  });

  it('links to the visualization dashboard of the given uuid', () => {
    const wrapper = mountBtn('abc-123');

    expect(wrapper.find('a').attributes('href')).toBe(
      `${window.location.origin}/visualization/d/abc-123?orgId=1`,
    );
  });

  it('url-encodes the uuid', () => {
    const wrapper = mountBtn('a/b c?d');

    expect(wrapper.find('a').attributes('href')).toBe(
      `${window.location.origin}/visualization/d/a%2Fb%20c%3Fd?orgId=1`,
    );
  });

  it('opens the link in a new tab with safe rel attributes', () => {
    const wrapper = mountBtn('abc-123');

    expect(wrapper.find('a').attributes('target')).toBe('_blank');
    expect(wrapper.find('a').attributes('rel')).toBe('noopener noreferrer');
  });

  it('shows the button label', () => {
    const wrapper = mountBtn('abc-123');

    expect(wrapper.find('a').text()).toContain('Open Visualization');
  });

  it('updates the href when the uuid changes', async () => {
    const wrapper = mountBtn('old');

    await wrapper.setProps({ uuid: 'new' });

    expect(wrapper.find('a').attributes('href')).toBe(
      `${window.location.origin}/visualization/d/new?orgId=1`,
    );
  });

  it('shows the link once a uuid is set and hides it again when removed', async () => {
    const wrapper = mountBtn();
    expect(wrapper.find('a').exists()).toBe(false);

    await wrapper.setProps({ uuid: 'abc-123' });
    expect(wrapper.find('a').exists()).toBe(true);

    await wrapper.setProps({ uuid: null });
    expect(wrapper.find('a').exists()).toBe(false);
  });
});
