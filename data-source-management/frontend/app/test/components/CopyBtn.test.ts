import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import CopyBtn from '@/components/CopyBtn.vue'; // adjust path

const { copyToClipboardMock, notifyMock } = vi.hoisted(() => ({
  copyToClipboardMock: vi.fn(),
  notifyMock: vi.fn(),
}));

vi.mock('quasar', async (importOriginal) => {
  const actual = await importOriginal<typeof import('quasar')>();
  return {
    ...actual,
    copyToClipboard: copyToClipboardMock,
    useQuasar: () => ({ notify: notifyMock }),
  };
});

installQuasarPlugin();

const mountCopyBtn = (props: { title?: string; textToCopy: string | null }) =>
  mount(CopyBtn, {
    props: { title: 'Copy ID', ...props },
    global: {
      // QTooltip normally renders in a portal on hover only
      stubs: { QTooltip: { template: '<div class="tooltip"><slot /></div>' } },
    },
  });

describe('CopyBtn', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    copyToClipboardMock.mockResolvedValue(undefined);
  });

  it('renders the title as tooltip text', () => {
    const wrapper = mountCopyBtn({ textToCopy: 'abc', title: 'Copy ID' });

    expect(wrapper.find('.tooltip').text()).toBe('Copy ID');
  });

  it('updates the tooltip when the title prop changes', async () => {
    const wrapper = mountCopyBtn({ textToCopy: 'abc', title: 'Copy ID' });

    await wrapper.setProps({ title: 'Copy URL' } as Record<string, unknown>);

    expect(wrapper.find('.tooltip').text()).toBe('Copy URL');
  });

  it('copies the new text after textToCopy changes', async () => {
    const wrapper = mountCopyBtn({ textToCopy: 'old' });

    await wrapper.setProps({ textToCopy: 'new' } as Record<string, unknown>);
    await wrapper.trigger('click');

    expect(copyToClipboardMock).toHaveBeenCalledTimes(1);
    expect(copyToClipboardMock).toHaveBeenCalledWith('new');
  });

  it('copies the text and notifies on success', async () => {
    const wrapper = mountCopyBtn({ textToCopy: 'abc-123' });

    await wrapper.trigger('click');
    await flushPromises();

    expect(copyToClipboardMock).toHaveBeenCalledWith('abc-123');
    expect(notifyMock).toHaveBeenCalledTimes(1);
    expect(notifyMock).toHaveBeenCalledWith({
      message: 'Copied to clipboard',
      color: 'positive',
      icon: 'check',
    });
  });

  it('notifies with an error when copying fails', async () => {
    copyToClipboardMock.mockRejectedValue(new Error('denied'));
    const wrapper = mountCopyBtn({ textToCopy: 'abc-123' });

    await wrapper.trigger('click');
    await flushPromises();

    expect(notifyMock).toHaveBeenCalledTimes(1);
    expect(notifyMock).toHaveBeenCalledWith({
      message: 'Failed to copy',
      color: 'negative',
      icon: 'error',
    });
  });

  it.each([null, ''])('does nothing when textToCopy is %j', async (value) => {
    const wrapper = mountCopyBtn({ textToCopy: value });

    await wrapper.trigger('click');
    await flushPromises();

    expect(copyToClipboardMock).not.toHaveBeenCalled();
    expect(notifyMock).not.toHaveBeenCalled();
  });
});
