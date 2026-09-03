<template>
  <ingest-form-http
    title="New HTTP Ingest"
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
import type { IngestHttpCreate } from 'src/services/ingest_http/types';
import { useIngestHttpStore } from 'stores/ingestHttpStore';
import IngestFormHttp from 'components/IngestFormHttp.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const httpStore = useIngestHttpStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestHttpCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_id: null,
  path_for_posts: null,
  file_type: null,
  api_key: null,
  enabled: null,
});

const isLoading = ref(false);

async function save() {
  const data: IngestHttpCreate = {
    permission_group_id: formData.value.permission_group_id,
    name: formData.value.name,
    description: formData.value.description,
    parser_id: formData.value.parser_id,
    path_for_posts: formData.value.path_for_posts,
    file_type: formData.value.file_type,
    api_key: formData.value.api_key,
    enabled: formData.value.enabled,
  };
  try {
    isLoading.value = true;
    const result = await httpStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    savedForm.value = { ...formData.value };
    // Navigate to detail
    await router.push(`/ingest/http/${result.id}`);
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
      message: 'Failed to create Ingest',
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
