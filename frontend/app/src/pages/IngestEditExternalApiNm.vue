<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit External Api Ingest</h5>
    <h6 class="q-mt-none">Neutron Monitor</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="detailRoute" />
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

          <permission-group-select
            v-model="formData.permission_group_id"
            :preselectedItem="itemPermissionGroup"
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
          <neutron-monitor-station-select
            v-model="formData.station_id"
            :preselectedItem="itemStation"
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
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
import type { IngestExternalApiNeutronMonitorUpdate } from 'src/services/ingest_external_api_neutron_monitor/types';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import NeutronMonitorStationSelect from 'components/NeutronMonitorStationSelect.vue';
import type { NeutronMonitorStation } from 'src/services/neutron_monitor_stations/type';
import type { PermissionGroup } from 'src/services/permission_group/types';

const ingestExternalApiNeutronMonitorStore = useIngestExternalApiNeutronMonitorStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const isLoading = ref(false);
const formData = ref<Partial<IngestExternalApiNeutronMonitorUpdate>>({
  name: '',
  permission_group_id: null,
  description: null,
  station_id: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  time_resolution_in_minutes: null,
});

const itemStation = ref<NeutronMonitorStation | null>(null);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await ingestExternalApiNeutronMonitorStore.dispatchGetOne(id);

      itemStation.value = data.station;
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: data.name || '',
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        station_id: data.station_id || null,
        sync_enabled: data.sync_enabled || false,
        sync_interval_in_minutes: data.sync_interval_in_minutes || null,
        time_resolution_in_minutes: data.time_resolution_in_minutes || null,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load ingest data',
      });
      await router.push('/ingest');
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/external-api-nm/${id}`;
  }
  return '';
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

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    let tmpTimeResolution = null;

    if (
      formData.value.time_resolution_in_minutes !== null &&
      formData.value.time_resolution_in_minutes !== undefined &&
      formData.value.time_resolution_in_minutes >= 0
    ) {
      tmpTimeResolution = formData.value.time_resolution_in_minutes;
    }
    const data: IngestExternalApiNeutronMonitorUpdate = {
      name: formData.value.name || '',
      description: formData.value.description || null,
      permission_group_id: formData.value.permission_group_id || null,
      station_id: formData.value.station_id || null,
      sync_enabled: formData.value.sync_enabled || false,
      sync_interval_in_minutes: formData.value.sync_interval_in_minutes || null,
      time_resolution_in_minutes: tmpTimeResolution,
    };

    isLoading.value = true;
    await ingestExternalApiNeutronMonitorStore.dispatchUpdate(id, data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate back to detail
    await router.push(detailRoute.value);
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
      message: 'Failed to update ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
