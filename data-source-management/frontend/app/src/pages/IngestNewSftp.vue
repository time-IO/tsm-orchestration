<template>
  <ingest-form-sftp
    title="New SFTP Ingest"
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
import type { IngestSftpCreate } from 'src/services/ingest_sftp/types';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
import IngestFormSftp from 'components/IngestFormSftp.vue';

const sftpStore = useIngestSftpStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestSftpCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_id: null,
  filename_pattern: null,
});

const isLoading = ref(false);

async function save() {
  const data: IngestSftpCreate = {
    permission_group_id: formData.value.permission_group_id,
    name: formData.value.name,
    description: formData.value.description,
    parser_id: formData.value.parser_id,
    filename_pattern: formData.value.filename_pattern,
  };
  try {
    isLoading.value = true;
    const result = await sftpStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate to detail
    await router.push(`/ingest/sftp/${result.id}`);
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
