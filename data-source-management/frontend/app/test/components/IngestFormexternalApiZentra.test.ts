import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { describe, expect, it } from 'vitest';

import IngestFormZentra from '@/components/IngestFormExternalApiZentra.vue';
import {
  describeExternalApiIngestForm,
  describePasswordToggle,
  HelpButtonStub,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { getBtn, findInput, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'Zentra ingest',
  permission_group_id: 1,
  description: '',
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  device_sn: 'z6-00001',
  period_in_minutes: 15,
  units: 'metric',
  api_key: 'secret-key',
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormZentra, makeModel, options);

describeExternalApiIngestForm(IngestFormZentra, makeModel);

describe('IngestFormZentra (Zentra specific)', () => {
  describe('v-model', () => {
    it('writes device serial number and API key back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Device Serial Number'), 'z6-00002');
      await typeInto(findInput(wrapper, 'API Key'), 'other-key');

      expect(formData.device_sn).toBe('z6-00002');
      expect(formData.api_key).toBe('other-key');
    });

    it('writes the period as a number, not a string', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Period'), '30');

      expect(formData.period_in_minutes).toBe(30);
    });

    it('switches the unit system with the toggle', async () => {
      const { wrapper, formData } = mountForm({ model: { units: 'metric' } });

      await getBtn(wrapper, 'Imperial').trigger('click');
      expect(formData.units).toBe('imperial');

      await getBtn(wrapper, 'Metric').trigger('click');
      expect(formData.units).toBe('metric');
    });
  });

  describe('help button', () => {
    it('connects the period help button to its term', () => {
      const { wrapper } = mountForm();
      const terms = wrapper.findAllComponents(HelpButtonStub).map((b) => b.props('termHelp'));

      expect(terms).toContain('period');
    });
  });

  describePasswordToggle(mountForm, 'API Key');

  describe('submit and validation', () => {
    it.each([
      ['an empty device serial number', { device_sn: '' }],
      ['an empty API key', { api_key: '' }],
      ['an empty period', { period_in_minutes: null }],
      ['a period of 0', { period_in_minutes: 0 }],
      ['a non-integer period', { period_in_minutes: 1.5 }],
    ] as Array<[string, Record<string, unknown>]>)(
      'does not emit save for %s',
      async (_, override) => {
        const { wrapper } = mountForm({ model: override });

        await submit(wrapper);

        expect(wrapper.emitted('save')).toBeUndefined();
      },
    );

    it('accepts the boundary value of 1 for the period', async () => {
      const { wrapper } = mountForm({ model: { period_in_minutes: 1 } });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });
  });
});
