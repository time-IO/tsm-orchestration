import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { describe, expect, it } from 'vitest';

import IngestFormMyAtmosphere from '@/components/IngestFormExternalApiMyAtmosphere.vue';
import {
  describeExternalApiIngestForm,
  describePasswordToggle,
  HelpButtonStub,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { findInput, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'MyAtmosphere ingest',
  permission_group_id: 1,
  description: '',
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  customer_id: 479,
  serial_number: '22935',
  period_in_minutes: 120,
  api_key: 'secret-key',
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormMyAtmosphere, makeModel, options);

describeExternalApiIngestForm(IngestFormMyAtmosphere, makeModel);

describe('IngestFormMyAtmosphere (MyAtmosphere specific)', () => {
  describe('v-model', () => {
    it('writes serial number and API key back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Device Serial Number'), '22938');
      await typeInto(findInput(wrapper, 'API Key'), 'other-key');

      expect(formData.serial_number).toBe('22938');
      expect(formData.api_key).toBe('other-key');
    });

    it('writes customer id and period as numbers, not strings', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Customer ID'), '480');
      await typeInto(findInput(wrapper, 'Period'), '30');

      expect(formData.customer_id).toBe(480);
      expect(formData.period_in_minutes).toBe(30);
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
      ['an empty customer id', { customer_id: null }],
      ['a customer id of 0', { customer_id: 0 }],
      ['a non-integer customer id', { customer_id: 1.5 }],
      ['an empty serial number', { serial_number: '' }],
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

    it('accepts the boundary value of 1 for customer id and period', async () => {
      const { wrapper } = mountForm({ model: { customer_id: 1, period_in_minutes: 1 } });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });
  });
});
