import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { describe, expect, it } from 'vitest';

import IngestFormTSystems from '@/components/IngestFormExternalApiTSystems.vue'; // adjust path
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
  name: 'TSystems ingest',
  permission_group_id: 1,
  description: null,
  group: 'group-1',
  station_id: 'station-1',
  tsystems_username: 'user',
  tsystems_password: 'secret',
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormTSystems, makeModel, options);

describeExternalApiIngestForm(IngestFormTSystems, makeModel, { syncIntervalEditable: false });

describe('IngestFormTSystems (TSystems specific)', () => {
  describe('v-model', () => {
    it('writes group, station id, username and password back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Group'), 'group-2');
      await typeInto(findInput(wrapper, 'Station ID'), 'station-2');
      await typeInto(findInput(wrapper, 'Username'), 'other-user');
      await typeInto(findInput(wrapper, 'Password'), 'other-secret');

      expect(formData.group).toBe('group-2');
      expect(formData.station_id).toBe('station-2');
      expect(formData.tsystems_username).toBe('other-user');
      expect(formData.tsystems_password).toBe('other-secret');
    });
  });

  describePasswordToggle(mountForm, 'Password');

  describe('submit and validation', () => {
    it.each([
      ['an empty group', { group: '' }],
      ['an empty station id', { station_id: '' }],
      ['an empty username', { tsystems_username: '' }],
      ['an empty password', { tsystems_password: '' }],
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
