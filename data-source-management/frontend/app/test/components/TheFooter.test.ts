import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { mount, RouterLinkStub } from '@vue/test-utils';
import { Screen } from 'quasar';
import { afterEach, describe, expect, it, vi } from 'vitest';

import TheFooter from '@/components/TheFooter.vue'; // adjust path

vi.mock('@/utils/public_asset', () => ({
  publicAsset: (path: string) => `/base/${path}`,
}));

installQuasarPlugin();

const stubs = {
  QFooter: { template: '<footer><slot /></footer>' },
  RouterLink: RouterLinkStub,
};

const mountFooter = () => mount(TheFooter, { global: { stubs } });

describe('TheFooter', () => {
  it.for([
    {
      alt: 'UFZ',
      href: 'https://www.ufz.de',
      src: '/base/images/UFZ_Logo_RGB_EN.png',
    },
    {
      alt: 'RDM',
      href: 'https://www.ufz.de/index.php?de=45348',
      src: '/base/images/259253_RDM_subline_fullcolor_rgb.png',
    },
  ])('renders the $alt logo with its asset path inside the correct link', (testCase) => {
    const wrapper = mountFooter();

    const img = wrapper.find(`a[href="${testCase.href}"]`).find('img');

    expect(img.attributes('alt')).toBe(testCase.alt);
    expect(img.attributes('src')).toBe(testCase.src);
  });

  it('it links to the legal notice and terms of use routes', () => {
    const wrapper = mountFooter();

    const links = wrapper
      .findAllComponents(RouterLinkStub)
      .map((link) => [link.text(), link.props('to')]);

    expect(links).toEqual([
      ['Legal Notice', { name: 'legal_notice' }],
      ['Terms of Use', { name: 'terms_of_use' }],
    ]);
  });

  it('links the privacy policy to the external UFZ page in a new tab', () => {
    const wrapper = mountFooter();

    const link = wrapper.find('a[href="https://www.ufz.de/index.php?en=44326"]');

    expect(link.text()).toBe('Privacy Policy');
    expect(link.attributes('target')).toBe('_blank');
  });

  it.for([
    { title: 'time.IO Repository', href: 'https://codebase.helmholtz.cloud/ufz-tsm' },
    { title: 'time.IO API', href: '/base/api/docs' },
    { title: 'Request Support', href: 'mailto:rdm-tsm@ufz.de' },
    {
      title: 'time.IO Wiki',
      href: 'https://codebase.helmholtz.cloud/ufz-tsm/timeio-support',
    },
  ])('has the "$title" icon link pointing to $href', (testCase) => {
    const wrapper = mountFooter();

    const link = wrapper.find(`a[title="${testCase.title}"]`);

    expect(link.attributes('href')).toBe(testCase.href);
    expect(link.attributes('target')).toBe('_blank');
  });
});

describe('icon size', () => {
  const originalLtMd = Screen.lt.md;

  afterEach(() => {
    Screen.lt.md = originalLtMd;
  });

  it.for([
    { ltMd: true, expected: '1.2rem' },
    { ltMd: false, expected: '1.5rem' },
  ])('uses icon size $expected when screen.lt.md is $ltMd', (testCase) => {
    Screen.lt.md = testCase.ltMd;

    const wrapper = mountFooter();

    const icons = wrapper.findAll('a[title] i');
    expect(icons).toHaveLength(4);
    for (const icon of icons) {
      expect(icon.attributes('style')).toContain(`font-size: ${testCase.expected}`);
    }
  });
});
