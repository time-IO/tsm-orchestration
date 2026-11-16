import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { QIcon } from 'quasar';
import { describe, expect, it } from 'vitest';

import IngestFormSensoto from '@/components/IngestFormExternalApiSensoto.vue'; // adjust path
import {
  describeExternalApiIngestForm,
  describePasswordToggle,
  HelpButtonStub,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { findInput, nativeValue, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'Sensoto ingest',
  permission_group_id: 1,
  description: null,
  organization: 'open',
  token: null,
  network: 'network-1',
  device: 'device-1',
  period_in_minutes: 15,
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormSensoto, makeModel, options);

describeExternalApiIngestForm(IngestFormSensoto, makeModel);

describe('IngestFormSensoto (Sensoto specific)', () => {
  describe('v-model', () => {
    it('writes organization, network and device back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Organization'), 'valigruen');
      await typeInto(findInput(wrapper, 'Network'), 'network-2');
      await typeInto(findInput(wrapper, 'Device'), 'device-2');

      expect(formData.organization).toBe('valigruen');
      expect(formData.network).toBe('network-2');
      expect(formData.device).toBe('device-2');
    });

    it('writes the token back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Token'), 'abc');

      expect(formData.token).toBe('abc');
    });

    // Guards the `.number` modifier on the period
    it('writes the period as a number, not a string', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Period'), '20');

      expect(formData.period_in_minutes).toBe(20);
    });
  });

  describe('defaults', () => {
    it('defaults the organization to "open" when no model is passed', () => {
      const { wrapper } = mountForm({ props: { modelValue: undefined } });

      expect(nativeValue(findInput(wrapper, 'Organization'))).toBe('open');
    });
  });

  describe('help buttons', () => {
    it('connects the period help button to its term', () => {
      const { wrapper } = mountForm();
      const terms = wrapper.findAllComponents(HelpButtonStub).map((b) => b.props('termHelp'));

      expect(terms).toContain('period');
    });
  });

  describe('token', () => {
    it('clears the token via the clear icon', async () => {
      const { wrapper, formData } = mountForm({ model: { token: 'abc' } });
      const clearIcon = findInput(wrapper, 'Token')
        .findAllComponents(QIcon)
        .find((i) => i.props('name') === 'cancel');
      if (!clearIcon) throw new Error('clear icon not found');

      await clearIcon.trigger('click');

      expect(formData.token).toBeNull();
    });
  });

  describePasswordToggle(mountForm, 'Token');

  describe('submit and validation', () => {
    it.each([
      ['an empty organization', { organization: '' }],
      ['an empty network', { network: '' }],
      ['an empty device', { device: '' }],
      ['an empty period', { period_in_minutes: null }],
      ['a negative period', { period_in_minutes: -1 }],
      ['a non-integer period', { period_in_minutes: 1.5 }],
    ] as Array<[string, Record<string, unknown>]>)(
      'does not emit save for %s',
      async (_, override) => {
        const { wrapper } = mountForm({ model: override });

        await submit(wrapper);

        expect(wrapper.emitted('save')).toBeUndefined();
      },
    );

    it('accepts the boundary value of 0 for the period', async () => {
      const { wrapper } = mountForm({ model: { period_in_minutes: 0 } });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });

    it('saves without a token because it is optional', async () => {
      const { wrapper } = mountForm({ model: { token: null } });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });
  });
});
