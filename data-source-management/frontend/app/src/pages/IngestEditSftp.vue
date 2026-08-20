<template>
  <ingest-form-sftp
    title="Edit SFTP Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    v-model="formData"
    @save="save"
    :item-permission-group="itemPermissionGroup"
    :item-parser="itemParser"
    :item-parser-id="formData.parser_id"
    :item-parser-type="itemParserType"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { IngestSftpUpdate } from 'src/services/ingest_sftp/types';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
import IngestFormSftp from 'components/IngestFormSftp.vue';
import type { PermissionGroup } from 'src/services/permission_group/types';
import type { ParserRead } from 'src/services/types';

const sftpStore = useIngestSftpStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestSftpUpdate>({
  name: null,
  permission_group_id: null,
  description: null,
  parser_id: null,
  filename_pattern: null,
});

const isLoading = ref(false);

const itemPermissionGroup = ref<PermissionGroup | null>(null);
const itemParserType = ref<string | null>(null);
const itemParser = ref<ParserRead | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await sftpStore.dispatchGetOne(id);

      itemPermissionGroup.value = data.permission_group || null;
      itemParser.value = data.parser;

      formData.value = {
        name: data.name || null,
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        filename_pattern: data.filename_pattern || null,
        parser_id: data.parser_id || null,
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
    return `/ingest/sftp/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestSftpUpdate = {
      permission_group_id: formData.value.permission_group_id || null,
      name: formData.value.name || null,
      description: formData.value.description || null,
      parser_id: formData.value.parser_id || null,
      filename_pattern: formData.value.filename_pattern || null,
    };

    isLoading.value = true;
    await sftpStore.dispatchUpdate(id, data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate to detail
    await router.push(detailRoute.value);
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
      message: 'Failed to update ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
