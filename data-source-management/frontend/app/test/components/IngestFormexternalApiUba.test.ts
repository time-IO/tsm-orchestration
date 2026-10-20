import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { config } from '@vue/test-utils';

import IngestFormUba from '@/components/IngestFormExternalApiUba.vue'; // adjust path
import {
  describeExternalApiIngestForm,
  describeFixedSyncInterval,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { findBtnsByIcon, findInput, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

const UBA_STATIONS_URL = 'https://luftdaten.umweltbundesamt.de/api/air-data/v3/stations/json';

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'UBA ingest',
  permission_group_id: 1,
  description: '',
  station_id: 'station-1',
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormUba, makeModel, options);

// The sync interval of UBA is a fixed, read-only field instead of an editable input
describeExternalApiIngestForm(IngestFormUba, makeModel, { syncIntervalEditable: false });

describe('IngestFormUba (UBA specific)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('v-model', () => {
    it('writes the station id back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Station ID'), 'station-2');

      expect(formData.station_id).toBe('station-2');
    });
  });

  describeFixedSyncInterval(mountForm);

  describe('browser effects', () => {
    it('opens the UBA station list in a new window', async () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
      const { wrapper } = mountForm();

      await findBtnsByIcon(wrapper, 'help_outline')[0]!.trigger('click');

      expect(openSpy).toHaveBeenCalledTimes(1);
      expect(openSpy).toHaveBeenCalledWith(UBA_STATIONS_URL, '_blank');
    });
  });

  describe('submit and validation', () => {
    it('does not emit save for an empty station id', async () => {
      const { wrapper } = mountForm({ model: { station_id: '' } });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toBeUndefined();
    });
  });

  describe('station id tooltip', () => {
    const originalStubs = config.global.stubs;

    beforeEach(() => {
      config.global.stubs = {
        ...originalStubs,
        QTooltip: { template: '<i class="tooltip"><slot/></i>' },
      };
    });

    afterEach(() => {
      config.global.stubs = originalStubs;
    });

    it('explains where to find the station id', () => {
      const { wrapper } = mountForm();

      const texts = wrapper.findAll('.tooltip').map((t) => t.text());

      expect(texts).toContain('View UBA station list (use "station id")');
    });
  });
});
