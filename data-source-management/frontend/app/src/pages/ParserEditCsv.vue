<template>
  <parser-form-csv
    title="Edit CSV Parser"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :permission-group-id="permissionGroupId"
    disable-permission-group
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { CsvParserCreate, CsvParserUpdate } from 'src/services/parser_csv/types';
import { useCsvParserStore } from 'stores/parserCsvStore';
import ParserFormCsv from 'components/ParserFormCsv.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

type CsvParserEditFormData = CsvParserUpdate & {
  permission_group_id?: number | null;
  timestamp_columns: CsvParserCreate['timestamp_columns'];
  comment: string[];
};

const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<CsvParserEditFormData>({
  name: null,
  description: null,
  delimiter: null,
  headlines_to_exclude: null,
  footlines_to_exclude: null,
  pandas_read_csv: null,
  timestamp_columns: [],
  header: null,
  comment: [],
  timezone: null,
  encoding: null,
});
const permissionGroupId = ref<number | null>(null);

const isLoading = ref(false);
const isSaving = ref(false);

const initialFormData = ref<CsvParserUpdate | null>(null);

const hasUnsavedChanges = computed(() => {
  if (!initialFormData.value) return false;
  return (
    JSON.stringify(normalizeFormData(formData.value)) !== JSON.stringify(initialFormData.value)
  );
});

useUnsavedChanges(() => hasUnsavedChanges.value && !isSaving.value);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await csvParserStore.dispatchGetOne(id);

      const loadedData = normalizeFormData(data);

      formData.value = loadedData;
      permissionGroupId.value = data.permission_group_id;
      initialFormData.value = structuredClone(loadedData);
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load parser data',
      });
      await router.push('/parser');
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/parser/csv/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: CsvParserUpdate = normalizeFormData(formData.value);

    isLoading.value = true;
    isSaving.value = true;

    await csvParserStore.dispatchUpdate(id, data);

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
      message: 'Failed to update parser',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}

function normalizeFormData(data: CsvParserUpdate): CsvParserEditFormData {
  return {
    name: data.name || null,
    description: data.description || null,
    delimiter: data.delimiter || null,
    headlines_to_exclude:
      data.headlines_to_exclude !== null && data.headlines_to_exclude !== undefined
        ? data.headlines_to_exclude
        : null,
    footlines_to_exclude:
      data.footlines_to_exclude !== null && data.footlines_to_exclude !== undefined
        ? data.footlines_to_exclude
        : null,
    pandas_read_csv: data.pandas_read_csv || null,
    timestamp_columns: (data.timestamp_columns || []).map((column) => ({
      column: column.column,
      timestamp_format: column.timestamp_format,
    })),
    header: data.header !== null && data.header !== undefined ? data.header : null,
    comment: [...(data.comment || [])],
    timezone: data.timezone || null,
    encoding: data.encoding || null,
  };
}
</script>

<style scoped></style>
