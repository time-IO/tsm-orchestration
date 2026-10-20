import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { config } from '@vue/test-utils';

import IngestFormDwd from '@/components/IngestFormExternalApiDwd.vue'; // adjust path
import {
  describeExternalApiIngestForm,
  HelpButtonStub,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { findBtnsByIcon, findInput, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

const DWD_STATIONS_URL =
  'https://opendata.dwd.de/climate_environment/CDC/help/RR_Stundenwerte_Beschreibung_Stationen.txt';

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'DWD ingest',
  permission_group_id: 1,
  description: '',
  station_id: '10381',
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  period_in_minutes: 15,
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormDwd, makeModel, options);

describeExternalApiIngestForm(IngestFormDwd, makeModel);

describe('IngestFormDwd (DWD specific)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('v-model', () => {
    it('writes the station id back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Station ID'), '04711');

      expect(formData.station_id).toBe('04711');
    });

    // Documents the current behavior: v-model on the period has no `.number` modifier,
    // so the model receives a string (unlike the Bosch form).
    it('writes the period back to the model (currently as string)', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Period'), '20');

      expect(formData.period_in_minutes).toBe('20');
    });
  });

  describe('help buttons', () => {
    it('connects the period help button to its term', () => {
      const { wrapper } = mountForm();
      const terms = wrapper.findAllComponents(HelpButtonStub).map((b) => b.props('termHelp'));

      expect(terms).toContain('period');
    });
  });

  describe('browser effects', () => {
    it('opens the DWD station list in a new window', async () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
      const { wrapper } = mountForm();

      await findBtnsByIcon(wrapper, 'help_outline')[0]!.trigger('click');

      expect(openSpy).toHaveBeenCalledTimes(1);
      expect(openSpy).toHaveBeenCalledWith(DWD_STATIONS_URL, '_blank');
    });
  });

  describe('submit and validation', () => {
    it.each([
      ['an empty station id', { station_id: '' }],
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

      expect(texts).toContain('View DWD station list (use Stations_id)');
    });
  });
});
