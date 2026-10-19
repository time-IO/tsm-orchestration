// test/components/TriggerExtApiDialog.test.ts
import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick } from 'vue';

import TriggerExtApiDialog from '@/components/TriggerExternalApiDialog.vue'; // adjust path

import { getBtn } from './utils/TestUtils';

const { dispatchTriggerApiMock, notifyMock } = vi.hoisted(() => ({
  dispatchTriggerApiMock: vi.fn(),
  notifyMock: vi.fn(),
}));

vi.mock('@/stores/externalApiTriggerStore', () => ({
  useTriggerExternalGenericApiStore: () => ({ dispatchTriggerApi: dispatchTriggerApiMock }),
}));

// Real Quasar components and date utils stay, only useQuasar is replaced to spy on notify
vi.mock('quasar', async (importOriginal) => {
  const actual = await importOriginal<typeof import('quasar')>();
  return {
    ...actual,
    useQuasar: () => ({ notify: notifyMock }),
  };
});

installQuasarPlugin();

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

// QDialog renders into a teleport. The stub renders the content inline while modelValue is true.
// Attributes like the keydown listeners fall through to the root element.
const QDialogStub = defineComponent({
  name: 'QDialog',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  setup:
    (props, { slots }) =>
    () =>
      props.modelValue ? h('div', { class: 'q-dialog-stub' }, slots.default?.()) : null,
});

// QTooltip only renders on hover, the stub renders its text inline
const QTooltipStub = defineComponent({
  name: 'QTooltip',
  setup:
    (_, { slots }) =>
    () =>
      h('span', { class: 'tooltip-stub' }, slots.default?.()),
});

// The picker has its own tests
const DateTimePickerStub = defineComponent({
  name: 'DateTimePicker',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'date-time-picker-stub' }),
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const IDS = [1, 2];

// "now" is fixed, so the default dates are deterministic
const NOW = new Date('2026-10-19T12:34:56Z');
const DEFAULT_BEGIN = '2026-10-12 00:00:00';
const DEFAULT_END = '2026-10-19 12:34:56';

const FORMAT_ERROR = 'Date has an invalid format (YYYY-MM-DD HH:MM:SS).';
const ORDER_ERROR = 'End date must be after begin date.';

const mountDialog = (props: Record<string, unknown> = {}) =>
  mount(TriggerExtApiDialog, {
    props: { modelValue: true, ids_to_trigger: IDS, ...props },
    global: {
      stubs: { QDialog: QDialogStub, QTooltip: QTooltipStub, DateTimePicker: DateTimePickerStub },
    },
  });

// The pickers have no label: index 0 is the begin date, index 1 the end date
const getPicker = (wrapper: ReturnType<typeof mountDialog>, index: 0 | 1) => {
  const picker = wrapper.findAllComponents(DateTimePickerStub)[index];
  if (!picker) throw new Error(`DateTimePicker #${index} not found`);
  return picker;
};

const setDates = async (wrapper: ReturnType<typeof mountDialog>, begin: string, end: string) => {
  getPicker(wrapper, 0).vm.$emit('update:modelValue', begin);
  getPicker(wrapper, 1).vm.$emit('update:modelValue', end);
  await nextTick();
};

const pressKey = (wrapper: VueWrapper, key: string) =>
  wrapper.find('.q-dialog-stub').trigger('keydown', { key });

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('TriggerExtApiDialog', () => {
  beforeEach(() => {
    // only Date is faked, flushPromises needs the real timers
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(NOW);
    dispatchTriggerApiMock.mockReset();
    dispatchTriggerApiMock.mockResolvedValue(undefined);
    notifyMock.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initialization', () => {
    it('shows the last seven days as default date range', () => {
      const wrapper = mountDialog();

      expect(getPicker(wrapper, 0).props('modelValue')).toBe(DEFAULT_BEGIN);
      expect(getPicker(wrapper, 1).props('modelValue')).toBe(DEFAULT_END);
    });

    it('renders no content while the dialog is closed', () => {
      const wrapper = mountDialog({ modelValue: false });

      expect(wrapper.find('.q-dialog-stub').exists()).toBe(false);
    });
  });

  describe('validation', () => {
    it('enables the button without tooltip for the default dates', () => {
      const wrapper = mountDialog();

      expect(getBtn(wrapper, 'Synchronise').props('disable')).toBe(false);
      expect(wrapper.find('.tooltip-stub').exists()).toBe(false);
    });

    it.each([
      ['a date without time', '2026-10-12', DEFAULT_END],
      ['a wrong separator', '2026/10/12 00:00:00', DEFAULT_END],
      ['an empty begin date', '', DEFAULT_END],
      ['an invalid end date', DEFAULT_BEGIN, 'tomorrow'],
    ])('disables the button and shows the format error for %s', async (_, begin, end) => {
      const wrapper = mountDialog();

      await setDates(wrapper, begin, end);

      expect(getBtn(wrapper, 'Synchronise').props('disable')).toBe(true);
      expect(wrapper.find('.tooltip-stub').text()).toBe(FORMAT_ERROR);
    });

    it('rejects a date that matches the format but does not exist', async () => {
      const wrapper = mountDialog();

      await setDates(wrapper, '2026-02-30 00:00:00', DEFAULT_END);

      expect(getBtn(wrapper, 'Synchronise').props('disable')).toBe(true);
      expect(wrapper.find('.tooltip-stub').text()).toBe(FORMAT_ERROR);
    });

    it('rejects an end date before the begin date', async () => {
      const wrapper = mountDialog();

      await setDates(wrapper, '2026-10-19 00:00:00', '2026-10-18 00:00:00');

      expect(getBtn(wrapper, 'Synchronise').props('disable')).toBe(true);
      expect(wrapper.find('.tooltip-stub').text()).toBe(ORDER_ERROR);
    });

    it('rejects an end date equal to the begin date', async () => {
      const wrapper = mountDialog();

      await setDates(wrapper, DEFAULT_BEGIN, DEFAULT_BEGIN);

      expect(wrapper.find('.tooltip-stub').text()).toBe(ORDER_ERROR);
    });

    it('enables the button again once the dates are valid', async () => {
      const wrapper = mountDialog();
      await setDates(wrapper, 'invalid', DEFAULT_END);

      await setDates(wrapper, DEFAULT_BEGIN, DEFAULT_END);

      expect(getBtn(wrapper, 'Synchronise').props('disable')).toBe(false);
      expect(wrapper.find('.tooltip-stub').exists()).toBe(false);
    });
  });

  describe('synchronise', () => {
    it('sends the ids and the dates to the store', async () => {
      const wrapper = mountDialog();
      await setDates(wrapper, '2026-10-01 00:00:00', '2026-10-05 12:00:00');

      await getBtn(wrapper, 'Synchronise').trigger('click');
      await flushPromises();

      expect(dispatchTriggerApiMock).toHaveBeenCalledTimes(1);
      expect(dispatchTriggerApiMock).toHaveBeenCalledWith({
        ingest_ids: IDS,
        start_date: '2026-10-01 00:00:00',
        end_date: '2026-10-05 12:00:00',
      });
    });

    it('notifies, emits success and closes the dialog after a successful sync', async () => {
      const wrapper = mountDialog();

      await getBtn(wrapper, 'Synchronise').trigger('click');
      await flushPromises();

      expect(notifyMock).toHaveBeenCalledTimes(1);
      expect(notifyMock).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'positive',
          message: 'External API was successfully synced.',
        }),
      );
      expect(wrapper.emitted('success')).toHaveLength(1);
      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });

    it('notifies and closes the dialog without success event when the store fails', async () => {
      dispatchTriggerApiMock.mockRejectedValue(new Error('boom'));
      const wrapper = mountDialog();

      await getBtn(wrapper, 'Synchronise').trigger('click');
      await flushPromises();

      expect(notifyMock).toHaveBeenCalledTimes(1);
      expect(notifyMock).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'negative',
          message: 'Failed to synchronise external API.',
        }),
      );
      expect(wrapper.emitted('success')).toBeUndefined();
      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });

    it('does nothing when there are no ids to trigger', async () => {
      const wrapper = mountDialog({ ids_to_trigger: [] });

      await getBtn(wrapper, 'Synchronise').trigger('click');
      await flushPromises();

      expect(dispatchTriggerApiMock).not.toHaveBeenCalled();
      expect(notifyMock).not.toHaveBeenCalled();
      expect(wrapper.emitted('success')).toBeUndefined();
    });

    it('does not call the store when the button is disabled', async () => {
      const wrapper = mountDialog();
      await setDates(wrapper, 'invalid', DEFAULT_END);

      await getBtn(wrapper, 'Synchronise').trigger('click');
      await flushPromises();

      expect(dispatchTriggerApiMock).not.toHaveBeenCalled();
    });
  });

  describe('closing', () => {
    it('closes the dialog when Cancel is clicked', async () => {
      const wrapper = mountDialog();

      await getBtn(wrapper, 'Cancel').trigger('click');

      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
      expect(dispatchTriggerApiMock).not.toHaveBeenCalled();
    });

    it('closes the dialog when Escape is pressed', async () => {
      const wrapper = mountDialog();

      await pressKey(wrapper, 'Escape');

      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });
  });

  describe('enter key', () => {
    // fails until triggerExtApiIfValid checks "!validationError.value"
    it('synchronises when Enter is pressed with valid dates', async () => {
      const wrapper = mountDialog();

      await pressKey(wrapper, 'Enter');
      await flushPromises();

      expect(dispatchTriggerApiMock).toHaveBeenCalledTimes(1);
    });

    // fails until triggerExtApiIfValid checks "!validationError.value"
    it('does not synchronise when Enter is pressed with invalid dates', async () => {
      const wrapper = mountDialog();
      await setDates(wrapper, 'invalid', DEFAULT_END);

      await pressKey(wrapper, 'Enter');
      await flushPromises();

      expect(dispatchTriggerApiMock).not.toHaveBeenCalled();
      expect(notifyMock).not.toHaveBeenCalled();
    });

    it('ignores other keys', async () => {
      const wrapper = mountDialog();

      await pressKey(wrapper, 'a');
      await flushPromises();

      expect(dispatchTriggerApiMock).not.toHaveBeenCalled();
    });
  });
});
