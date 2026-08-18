<template>
  <ingest-form-external-api-t-systems
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
import type { IngestExternalApiTSystemsCreate } from 'src/services/ingest_external_api_tsystems/types';
import { useIngestExternalApiTSystemsStore } from 'stores/ingestExternalApiTSystemsStore';
import IngestFormExternalApiTSystems from 'components/IngestFormExternalApiTSystems.vue';

const tsystemsStore = useIngestExternalApiTSystemsStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalApiTSystemsCreate>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  sync_interval_in_minutes: 60,
  group: null,
  station_id: null,
  tsystems_username: null,
  tsystems_password: null,
});

const isLoading = ref(false);

async function save() {
  const data: IngestExternalApiTSystemsCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    group: formData.value.group,
    station_id: formData.value.station_id,
    tsystems_username: formData.value.tsystems_username,
    tsystems_password: formData.value.tsystems_password,
  };
  try {
    isLoading.value = true;
    const result = await tsystemsStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to list
    await router.push(`/ingest/external-api/tsystems/${result.id}`);
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
