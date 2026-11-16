import { installQuasarPlugin } from '@quasar/quasar-app-extension-testing-unit-vitest';
import { QIcon } from 'quasar';
import { describe, expect, it } from 'vitest';

import IngestFormBosch from '@/components/IngestFormExternalApiBosch.vue'; // adjust path
import {
  describeExternalApiIngestForm,
  HelpButtonStub,
  mountIngestForm,
  type MountOptions,
  type ModelFactory,
} from './utils/TestFormSuiteForIngestExternalApi';
import { findInput, submit, typeInto } from './utils/TestUtils';

installQuasarPlugin();

const makeModel: ModelFactory = (overrides = {}) => ({
  name: 'Bosch ingest',
  permission_group_id: 1,
  description: 'Some description',
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  endpoint: 'https://api.example.com',
  sensor_id: 'sensor-1',
  bosch_username: 'user',
  bosch_password: 'secret',
  period_in_minutes: 15,
  ...overrides,
});

const mountForm = (options: MountOptions = {}) =>
  mountIngestForm(IngestFormBosch, makeModel, options);

describeExternalApiIngestForm(IngestFormBosch, makeModel);

describe('IngestFormBosch (Bosch specific)', () => {
  describe('v-model', () => {
    it('writes sensor id, username and password back to the model', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Sensor-ID'), 'sensor-2');
      await typeInto(findInput(wrapper, 'Username'), 'other-user');
      await typeInto(findInput(wrapper, 'Password'), 'other-secret');

      expect(formData.sensor_id).toBe('sensor-2');
      expect(formData.bosch_username).toBe('other-user');
      expect(formData.bosch_password).toBe('other-secret');
    });

    it('writes endpoint and period back to the model (period as number)', async () => {
      const { wrapper, formData } = mountForm();

      await typeInto(findInput(wrapper, 'Endpoint'), 'https://new.example.com');
      await typeInto(findInput(wrapper, 'Period'), '20');

      expect(formData.endpoint).toBe('https://new.example.com');
      expect(formData.period_in_minutes).toBe(20);
    });
  });

  describe('help button', () => {
    it('connects the period help button to its term', () => {
      const { wrapper } = mountForm();
      const terms = wrapper.findAllComponents(HelpButtonStub).map((b) => b.props('termHelp'));

      expect(terms).toContain('period');
    });
  });

  describe('password visibility', () => {
    it('masks the password by default and toggles it via the icon', async () => {
      const { wrapper } = mountForm();
      const password = findInput(wrapper, 'Password');

      expect(password.find('input').attributes('type')).toBe('password');
      expect(password.findComponent(QIcon).props('name')).toBe('visibility_off');

      await password.findComponent(QIcon).trigger('click');

      expect(password.find('input').attributes('type')).toBe('text');
      expect(password.findComponent(QIcon).props('name')).toBe('visibility');

      await password.findComponent(QIcon).trigger('click');

      expect(password.find('input').attributes('type')).toBe('password');
    });
  });

  describe('submit and validation', () => {
    it.each([
      ['an empty sensor id', { sensor_id: '' }],
      ['an empty username', { bosch_username: '' }],
      ['an empty password', { bosch_password: '' }],
      ['an empty endpoint', { endpoint: '' }],
      ['a non-HTTPS endpoint', { endpoint: 'http://api.example.com' }],
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
});
