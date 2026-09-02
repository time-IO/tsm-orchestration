<template>
  <ingest-form-external-api-nm
    title="New External Api Ingest"
    :is-loading="isLoading"
    back-route="/ingest/new"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
import type { IngestExternalApiNeutronMonitorCreate } from 'src/services/ingest_external_api_neutron_monitor/types';
import IngestFormExternalApiNm from 'components/IngestFormExternalApiNm.vue';

const ingestExternalApiNeutronMonitorStore = useIngestExternalApiNeutronMonitorStore();
const $q = useQuasar();
const router = useRouter();

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
    await router.push(`/ingest/external-api/nm/${result.id}`);
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
      message: 'Failed to create Ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
