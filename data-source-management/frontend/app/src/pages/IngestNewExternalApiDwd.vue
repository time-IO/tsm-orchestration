<template>
  <ingest-form-external-api-dwd
    title="New External Api Ingest"
    :is-loading="isLoading"
    back-route="/ingest/new"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { IngestExternalApiDwdCreate } from 'src/services/ingest_external_api_dwd/types';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useIngestExternalApiDwdStore } from 'stores/ingestExternalApiDwdStore';
import IngestFormExternalApiDwd from 'components/IngestFormExternalApiDwd.vue';

const dwdStore = useIngestExternalApiDwdStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalApiDwdCreate>({
  name: '',
  permission_group_id: null,
  description: '',
  station_id: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  period_in_minutes: null,
});
const isLoading = ref(false);

async function save() {
  const data: IngestExternalApiDwdCreate = {
    name: formData.value.name,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    station_id: formData.value.station_id,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    period_in_minutes: formData.value.period_in_minutes,
  };
  try {
    isLoading.value = true;
    const result = await dwdStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to list
    await router.push(`/ingest/external-api/dwd/${result.id}`);
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
