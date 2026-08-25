<template>
  <ingest-form-external-api-bosch
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
import { useIngestExternalApiBoschStore } from 'stores/ingestExternalApiBoschStore';
import type { IngestExternalApiBoschCreate } from 'src/services/ingest_external_api_bosch/types';
import IngestFormExternalApiBosch from 'components/IngestFormExternalApiBosch.vue';

const boschStore = useIngestExternalApiBoschStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalApiBoschCreate>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  endpoint: null,
  sensor_id: null,
  bosch_username: null,
  bosch_password: null,
  period_in_minutes: null,
});

const isLoading = ref(false);

async function save() {
  const data: IngestExternalApiBoschCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    endpoint: formData.value.endpoint,
    sensor_id: formData.value.sensor_id,
    bosch_username: formData.value.bosch_username,
    bosch_password: formData.value.bosch_password,
    period_in_minutes: formData.value.period_in_minutes,
  };
  try {
    isLoading.value = true;
    const result = await boschStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to list
    await router.push(`/ingest/external-api/bosch/${result.id}`);
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
