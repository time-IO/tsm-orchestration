<template>
  <ingest-form-external-api-uba
    title="New External Api Ingest"
    :is-loading="isLoading"
    backRoute="/ingest/new"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { IngestExternalApiUbaCreate } from 'src/services/ingest_external_api_uba/types';
import { useIngestExternalApiUbaStore } from 'stores/ingestExternalApiUbaStore';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import IngestFormExternalApiUba from 'components/IngestFormExternalApiUba.vue';

const ubaStore = useIngestExternalApiUbaStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalApiUbaCreate>({
  name: '',
  permission_group_id: null,
  description: '',
  station_id: null,
  sync_enabled: false,
});
const isLoading = ref(false);

async function save() {
  const data: IngestExternalApiUbaCreate = {
    name: formData.value.name,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    station_id: formData.value.station_id,
    sync_enabled: formData.value.sync_enabled,
  };
  try {
    isLoading.value = true;
    const result = await ubaStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate back to list
    await router.push(`/ingest/external-api/uba/${result.id}`);
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
