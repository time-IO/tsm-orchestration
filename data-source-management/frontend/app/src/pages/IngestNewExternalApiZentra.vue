<template>
  <ingest-form-external-api-zentra
    title="New External Api Ingest"
    :is-loading="isLoading"
    back-route="/ingest/new"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { IngestExternalApiZentraCreate } from '@/services/ingest_external_api_zentra/types';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useIngestExternalApiZentraStore } from '@/stores/ingestExternalApiZentraStore';
import IngestFormExternalApiZentra from '@/components/IngestFormExternalApiZentra.vue';
import { useUnsavedChanges } from '@/composables/useUnsavedChanges';

const zenStore = useIngestExternalApiZentraStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalApiZentraCreate>({
  name: '',
  permission_group_id: null,
  description: '',
  device_sn: '',
  period_in_minutes: null,
  units: 'metric',
  sync_enabled: false,
  sync_interval_in_minutes: null,
  api_key: '',
});
const isLoading = ref(false);

async function save() {
  const data: IngestExternalApiZentraCreate = {
    name: formData.value.name,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    device_sn: formData.value.device_sn,
    period_in_minutes: formData.value.period_in_minutes,
    units: formData.value.units,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    api_key: formData.value.api_key,
  };
  try {
    isLoading.value = true;
    const result = await zenStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    savedForm.value = { ...formData.value };
    // Navigate back to list
    await router.push(`/ingest/external-api/Zentra/${result.id}`);
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

const savedForm = ref({ ...formData.value });
useUnsavedChanges(() => JSON.stringify(formData.value) !== JSON.stringify(savedForm.value));
</script>

<style scoped></style>
