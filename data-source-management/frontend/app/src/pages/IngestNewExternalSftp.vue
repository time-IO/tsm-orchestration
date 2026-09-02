<template>
  <ingest-form-external-sftp
    title="New External SFTP Ingest"
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
import type { IngestExternalSftpCreate } from 'src/services/ingest_external_sftp/types';
import { useIngestExternalSftpStore } from 'stores/ingestExternalSftpStore';
import IngestFormExternalSftp from 'components/IngestFormExternalSftp.vue';

const ingestExternalSftpStore = useIngestExternalSftpStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalSftpCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_id: null,
  filename_pattern: null,
  uri: null,
  path: null,
  password: null,
  username: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
});

const isLoading = ref(false);

async function save() {
  const data: IngestExternalSftpCreate = {
    permission_group_id: formData.value.permission_group_id,
    name: formData.value.name,
    description: formData.value.description,
    parser_id: formData.value.parser_id,
    filename_pattern: formData.value.filename_pattern,
    uri: formData.value.uri,
    path: formData.value.path,
    password: formData.value.password,
    username: formData.value.username,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
  };
  try {
    isLoading.value = true;
    const result = await ingestExternalSftpStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate to detail
    await router.push(`/ingest/external-sftp/${result.id}`);
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
