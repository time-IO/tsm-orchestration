<template>
  <ingest-form-sftp
    title="Copy SFTP Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    v-model="formData"
    :item-permission-group="itemPermissionGroup"
    :item-parser="itemParser"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { IngestSftpCreate } from 'src/services/ingest_sftp/types';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
import IngestFormSftp from 'components/IngestFormSftp.vue';
import type { PermissionGroup } from 'src/services/permission_group/types';
import type { ParserRead } from 'src/services/types';

const sftpStore = useIngestSftpStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestSftpCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_id: null,
  filename_pattern: null,
});

const isLoading = ref(false);

const itemPermissionGroup = ref<PermissionGroup | null>(null);
const itemParser = ref<ParserRead | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await sftpStore.dispatchGetOne(id);

      itemPermissionGroup.value = data.permission_group;
      itemParser.value = data.parser;

      formData.value = {
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        filename_pattern: data.filename_pattern,
        parser_id: data.parser_id,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load Ingest Data',
      });
      await router.push('/ingest');
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/sftp/${id}`;
  }
  return '';
});

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
      message: 'Failed to create ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
