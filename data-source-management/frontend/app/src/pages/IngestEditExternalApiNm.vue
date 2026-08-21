<template>
  <ingest-form-external-api-nm
    title="Edit External Api Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :item-permission-group="itemPermissionGroup"
    :item-station="itemStation"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
import type { IngestExternalApiNeutronMonitorUpdate } from 'src/services/ingest_external_api_neutron_monitor/types';
import type { NeutronMonitorStation } from 'src/services/neutron_monitor_stations/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiNm from 'components/IngestFormExternalApiNm.vue';

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
    return `/ingest/external-api/nm/${id}`;
  }
  return '';
});

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
      timeout: 0,
      actions: [
        {
          icon: 'close',
          color: 'white',
          round: true,
          handler: () => {},
        },
      ],
      message: 'Failed to update ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
