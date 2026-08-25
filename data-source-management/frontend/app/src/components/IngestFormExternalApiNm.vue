<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <h6 class="q-mt-none">Neutron Monitor</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>
    <p>
      For more information on Neutronmonitor API properties, visit the API documentation
      <a href="https://www.nmdb.eu/nest/help.php#howto" target="_blank">here</a>.
    </p>
    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="$emit('save')" class="q-gutter-md">
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this Ingest"
            :rules="[rules.REQUIRED, ruleFactories.MAX(80)]"
          />

          <permission-group-select
            v-model="formData.permission_group_id"
            :preselected-item="itemPermissionGroup"
            :rules="[rules.REQUIRED]"
          />

          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this Ingest Configuration"
          />

          <q-separator class="q-my-lg" />
          <neutron-monitor-station-select
            v-model="formData.station_id"
            :preselected-item="itemStation"
          />
          <q-select
            outlined
            class="q-mb-md"
            v-model="formData.time_resolution_in_minutes"
            :options="timeResolutionOptions"
            label="Time Resolution (in minutes)"
            emit-value
            map-options
            option-value="value"
            option-label="label"
          />

          <!-- Sync Settings -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">Synchronization Settings</div>

            <q-toggle
              v-model="formData.sync_enabled"
              label="Enable File Server Sync"
              color="primary"
              size="md"
            />

            <div class="q-mt-md">
              <q-input
                filled
                v-model.number="formData.sync_interval_in_minutes"
                label="Sync Interval (in minutes) *"
                type="number"
                :rules="[rules.REQUIRED, rules.INTEGER, ruleFactories.MIN(10)]"
              >
                <template #append>
                  <help-button termHelp="sync_interval" />
                </template>
              </q-input>
            </div>
          </q-card-section>

          <!-- Action Buttons -->
          <div class="row q-mt-lg">
            <q-space />
            <div class="col-6">
              <q-btn
                unelevated
                color="green"
                type="submit"
                :loading="isLoading"
                label="Save"
                class="full-width"
              />
            </div>
            <q-space />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import NeutronMonitorStationSelect from 'components/NeutronMonitorStationSelect.vue';
import type {
  IngestExternalApiNeutronMonitorCreate,
  IngestExternalApiNeutronMonitorUpdate,
} from 'src/services/ingest_external_api_neutron_monitor/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import type { NeutronMonitorStation } from 'src/services/neutron_monitor_stations/types';
import HelpButton from 'components/HelpButton.vue';
import { ruleFactories, rules } from 'src/utils/validation/rules';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
  itemStation?: NeutronMonitorStation | null;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<
  IngestExternalApiNeutronMonitorCreate | IngestExternalApiNeutronMonitorUpdate
>({
  default: {
    name: '',
    permission_group_id: null,
    description: null,
    station_id: null,
    sync_enabled: false,
    sync_interval_in_minutes: null,
    time_resolution_in_minutes: null,
  },
});

const timeResolutionOptions = [
  { value: -1, label: 'none' },
  { value: 0, label: '0' },
  { value: 2, label: '2' },
  { value: 5, label: '5' },
  { value: 10, label: '10' },
  { value: 30, label: '30' },
  { value: 60, label: '60' },
  { value: 120, label: '120' },
  { value: 360, label: '360' },
  { value: 720, label: '720' },
  { value: 1440, label: '1440' },
  { value: 39276, label: '39276' },
  { value: 525969, label: '525969' },
];
</script>

<style scoped></style>
