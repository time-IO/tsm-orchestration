<template>
  <ingest-form-external-sftp
    title="Copy External SFTP Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :item-permission-group="itemPermissionGroup"
    :item-parser="itemParser"
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
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalSftp from 'components/IngestFormExternalSftp.vue';
import type { ParserRead } from 'src/services/types';

const ingestExternalSftpStore = useIngestExternalSftpStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

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

const itemPermissionGroup = ref<PermissionGroup | null>(null);
const itemParser = ref<ParserRead | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await ingestExternalSftpStore.dispatchGetOne(id);

      itemPermissionGroup.value = data.permission_group;
      itemParser.value = data.parser;

      formData.value = {
        permission_group_id: data.permission_group_id,
        name: `${data.name} - Copy`,
        description: data.description,
        parser_id: data.parser_id,
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
