<template>
  <ingest-form-external-sftp
    title="Copy External SFTP Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { IngestExternalSftpCreate } from 'src/services/ingest_external_sftp/types';
import { useIngestExternalSftpStore } from 'stores/ingestExternalSftpStore';
import type { CsvParserPublic } from 'src/services/parser_csv/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalSftp from 'components/IngestFormExternalSftp.vue';

const ingestExternalSftpStore = useIngestExternalSftpStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestExternalSftpCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_csv_id: null,
  filename_pattern: null,
  uri: null,
  path: null,
  password: null,
  username: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
});

const isLoading = ref(false);

const permissionGroupId = ref<number | null>(null);
const itemParser = ref<CsvParserPublic | null>(null);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await ingestExternalSftpStore.dispatchGetOne(id);

      itemParser.value = data.csv_parser;
      permissionGroupId.value = data.permission_group_id || null;
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        permission_group_id: data.permission_group_id,
        name: `${data.name} - Copy`,
        description: data.description,
        parser_csv_id: data.parser_csv_id,
        filename_pattern: data.filename_pattern,
        uri: data.uri,
        path: data.path,
        password: null,
        username: null,
        sync_enabled: data.sync_enabled,
        sync_interval_in_minutes: data.sync_interval_in_minutes,
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
    return `/ingest/external-sftp/${id}`;
  }
  return '';
});

async function save() {
  const data: IngestExternalSftpCreate = {
    permission_group_id: formData.value.permission_group_id,
    name: formData.value.name,
    description: formData.value.description,
    parser_csv_id: formData.value.parser_csv_id,
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
