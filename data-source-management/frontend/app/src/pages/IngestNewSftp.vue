<template>
  <ingest-form-sftp
    title="New SFTP Ingest"
    :is-loading="isLoading"
    :back-route="backRoute"
    v-model="formData"
    :item-parser="itemParser"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter, useRoute } from 'vue-router';
import type { ParserRead } from '@/services/types';
import type { IngestSftpCreate } from '@/services/ingest_sftp/types';
import { useCsvParserStore } from '@/stores/parserCsvStore';
import { useJsonParserStore } from '@/stores/parserJsonStore';
import { useSoilcanParserStore } from '@/stores/parserSoilcanStore';
import { useIngestSftpStore } from '@/stores/ingestSftpStore';
import IngestFormSftp from '@/components/IngestFormSftp.vue';

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
const itemParser = ref<ParserRead | null>(null);

const csvParserStore = useCsvParserStore();
const jsonParserStore = useJsonParserStore();
const soilcanParserStore = useSoilcanParserStore();

const parserStoresByType: Record<
  string,
  typeof csvParserStore | typeof jsonParserStore | typeof soilcanParserStore
> = {
  csv: csvParserStore,
  json: jsonParserStore,
  soilcan: soilcanParserStore,
};

const backRoute = computed(() => {
  const parserId = route.query.parserId as string | undefined;
  const parserType = route.query.parserType as string | undefined;

  if (parserId && parserType) {
    return `/parser/${parserType}/${parserId}`;
  }
  return '/ingest/new';
});

onMounted(async () => {
  const parserId = route.query.parserId;
  const parserType = route.query.parserType as string | undefined;

  if (parserId && parserType && parserStoresByType[parserType]) {
    try {
      const parser = await parserStoresByType[parserType].dispatchGetOne(Number(parserId));
      itemParser.value = { ...parser, parser_type: parserType };
      formData.value.parser_id = parser.id;
      formData.value.permission_group_id = parser.permission_group_id ?? null;
    } catch {
      $q.notify({
        position: 'top',
        type: 'negative',
        message: 'Failed to preselect parser',
      });
    }
  }
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
      message: 'Failed to create Ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
