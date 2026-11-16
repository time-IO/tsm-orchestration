import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { flushPromises } from '@vue/test-utils';
import { QSelect } from 'quasar';
import { describe, expect, it } from 'vitest';
import { defineComponent, h } from 'vue';

import IngestFormNeutronMonitor from '@/components/IngestFormExternalApiNm.vue'; // adjust path
import {
  describeExternalApiIngestForm,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { submit } from './utils/TestUtils';

installQuasarPlugin();

const NeutronMonitorStationSelectStub = defineComponent({
  name: 'NeutronMonitorStationSelect',
  props: {
    modelValue: { type: null, default: null },
    preselectedItem: { type: null, default: null },
  },
  emits: ['update:modelValue'],
  setup: () => () => h('div', { class: 'station-select-stub' }),
});

const stubs = { NeutronMonitorStationSelect: NeutronMonitorStationSelectStub };

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'Neutron ingest',
  permission_group_id: 1,
  description: null,
  station_id: 3,
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  time_resolution_in_minutes: null,
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormNeutronMonitor, makeModel, { ...options, stubs });

describeExternalApiIngestForm(IngestFormNeutronMonitor, makeModel, { stubs });

describe('IngestFormNeutronMonitor (Neutron Monitor specific)', () => {
  describe('station select', () => {
    it('passes the model station id and the preselected station to the station select', () => {
      const station = { id: 3, name: 'Station' };
      const { wrapper } = mountForm({ props: { itemStation: station } });
      const select = wrapper.findComponent(NeutronMonitorStationSelectStub);

      expect(select.props('modelValue')).toBe(3);
      expect(select.props('preselectedItem')).toEqual(station);
    });

    it('writes the selected station back to the model', async () => {
      const { wrapper, formData } = mountForm();

      wrapper.findComponent(NeutronMonitorStationSelectStub).vm.$emit('update:modelValue', 7);
      await flushPromises();

      expect(formData.station_id).toBe(7);
    });
  });

  describe('time resolution', () => {
    it('offers "none" as -1 and the numeric resolutions as options', () => {
      const { wrapper } = mountForm();
      const options = wrapper.findComponent(QSelect).props('options') as Array<{
        value: number;
        label: string;
      }>;

      expect(options[0]).toEqual({ value: -1, label: 'none' });
      expect(options.map((o) => o.value)).toContain(60);
    });

    it('writes the selected value (not the label object) back to the model', async () => {
      const { wrapper, formData } = mountForm();

      wrapper.findComponent(QSelect).vm.$emit('update:modelValue', 60);
      await flushPromises();

      expect(formData.time_resolution_in_minutes).toBe(60);
    });

    it('is optional: saves with an empty time resolution', async () => {
      const { wrapper } = mountForm({ model: { time_resolution_in_minutes: null } });

      await submit(wrapper);

      expect(wrapper.emitted('save')).toHaveLength(1);
    });
  });
});
