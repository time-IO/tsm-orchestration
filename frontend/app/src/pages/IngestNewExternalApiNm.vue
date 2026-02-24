<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
    <h6 class="q-mt-none">Neutron Monitor</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new" />
      </div>
    </div>
    <p>
      For more information on Neutronmonitor API properties, visit the API documentation
      <a href="https://www.nmdb.eu/nest/help.php#howto" target="_blank">here</a>.
    </p>
    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="save" class="q-gutter-md">
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this ingest"
            :rules="[(val) => !!val || 'Name is required']"
          />

          <q-select
            filled
            v-model="formData.permission_group_id"
            :options="permissionGroupStore.permissionGroups"
            label="Permission Group *"
            option-value="id"
            option-label="name"
            emit-value
            map-options
            hint="Select the permission group this ingest belongs to"
            :rules="[(val) => !!val || 'Permission group is required']"
          />

          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this ingest configuration"
          />

          <q-separator class="q-my-lg" />
          <q-select
            outlined
            class="q-mb-md"
            v-model="formData.station_id"
            use-input
            emit-value
            map-options
            clearable
            :options="filteredNeutronMonitorStationOptions"
            @filter="filterNeutronMonitorStation"
            option-value="id"
            option-label="station_id"
            label="Select a station *"
            :rules="[(val) => !!val || 'Station is required']"
          >
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps" clickable>
                <q-item-section>
                  <q-item-label>{{ scope.opt.station_id }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey"> No results </q-item-section>
              </q-item>
            </template>
          </q-select>
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
                :disable="!formData.sync_enabled"
                v-model.number="formData.sync_interval_in_minutes"
                :label="
                  formData.sync_enabled
                    ? 'Sync Interval (in minutes) *'
                    : 'Sync Interval (in minutes)'
                "
                type="number"
                :rules="[
                  (val) =>
                    !formData.sync_enabled ||
                    (val !== null && val !== '' && val > 0) ||
                    'Interval must be a positive number when sync is enabled',
                ]"
              />
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
import { onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useNeutronMonitorStationStore } from 'stores/neutronMonitorStationStore';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import type { IngestExternalApiNeutronMonitorCreate } from 'src/services/ingest_external_api_neutron_monitor/types';

const neutronMonitorStationStore = useNeutronMonitorStationStore();
const permissionGroupStore = usePermissionGroupStore();
const ingestExternalApiNeutronMonitorStore = useIngestExternalApiNeutronMonitorStore();
const $q = useQuasar();
const router = useRouter();

const filteredNeutronMonitorStationOptions = ref([
  ...neutronMonitorStationStore.neutronMonitorStations,
]);

const isLoading = ref(false);
const formData = ref<IngestExternalApiNeutronMonitorCreate>({
  name: '',
  permission_group_id: null,
  description: null,
  station_id: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  time_resolution_in_minutes: null,
});

onMounted(async () => {
  try {
    await neutronMonitorStationStore.dispatchGetList();
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch neutron monitor stations',
    });
  }

  try {
    await permissionGroupStore.dispatchGetList();
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch permission groups',
    });
  }
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

function filterNeutronMonitorStation(val: string, update: (callback: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredNeutronMonitorStationOptions.value = [
        ...neutronMonitorStationStore.neutronMonitorStations,
      ];
    });
    return;
  }

  update(() => {
    const needle = val.toLowerCase();
    filteredNeutronMonitorStationOptions.value =
      neutronMonitorStationStore.neutronMonitorStations.filter((v) =>
        v.station_id.toLowerCase().includes(needle),
      );
  });
}

async function save() {
  const data: IngestExternalApiNeutronMonitorCreate = {
    name: formData.value.name,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    station_id: formData.value.station_id,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    time_resolution_in_minutes:
      formData.value.time_resolution_in_minutes === -1
        ? null
        : formData.value.time_resolution_in_minutes,
  };

  try {
    isLoading.value = true;
    const result = await ingestExternalApiNeutronMonitorStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate back to detail
    await router.push(`/ingest/external-api-nm/${result.id}`);
  } catch (error) {
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    let errorCaption = error?.response?.data?.detail || '';

    // if it is a validation error, then error.response.data.detail is an array of objects [{type:string, loc: string[], msg: string, input: any, probably an object}]
    if (typeof errorCaption === 'object') {
      errorCaption = errorCaption[0].msg;
    }

    $q.notify({
      position: 'top',
      type: 'negative',
      progress: true,
      message: 'Failed to create ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
