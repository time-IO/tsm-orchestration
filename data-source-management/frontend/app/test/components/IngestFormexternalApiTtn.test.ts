import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { describe, expect, it } from 'vitest';

import IngestFormTheThingsNetwork from '@/components/IngestFormExternalApiTtn.vue'; // adjust path
import {
  describeExternalApiIngestForm,
  describePasswordToggle,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { findInput, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'TTN ingest',
  permission_group_id: 1,
  description: null,
  endpoint_uri: 'https://eu1.cloud.thethings.network',
  api_key: 'secret-key',
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormTheThingsNetwork, makeModel, options);

describeExternalApiIngestForm(IngestFormTheThingsNetwork, makeModel);

describe('IngestFormTheThingsNetwork (TTN specific)', () => {
  describe('v-model', () => {
    it('writes endpoint uri and api key back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Endpoint-URI'), 'https://new.example.com');
      await typeInto(findInput(wrapper, 'API-Key'), 'other-key');

      expect(formData.endpoint_uri).toBe('https://new.example.com');
      expect(formData.api_key).toBe('other-key');
    });
  });

  describePasswordToggle(mountForm, 'API-Key');

  describe('submit and validation', () => {
    it.each([
      ['an empty endpoint uri', { endpoint_uri: '' }],
      ['a non-HTTPS endpoint uri', { endpoint_uri: 'http://eu1.cloud.thethings.network' }],
      ['an empty api key', { api_key: '' }],
    ] as Array<[string, Record<string, unknown>]>)(
      'does not emit save for %s',
      async (_, override) => {
        const { wrapper } = mountForm({ model: override });

        await submit(wrapper);

        expect(wrapper.emitted('save')).toBeUndefined();
      },
    );
  });
});
