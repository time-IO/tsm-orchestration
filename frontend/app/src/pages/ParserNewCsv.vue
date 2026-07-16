<template>
  <parser-form-csv
    title="New CSV Parser"
    :is-loading="isLoading"
    back-route="/parser/new"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import type { CsvParserCreate } from 'src/services/parser_csv/types';
import { useCsvParserStore } from 'stores/parserCsvStore';
import ParserFormCsv from 'components/ParserFormCsv.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<CsvParserCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  delimiter: null,
  headlines_to_exclude: null,
  footlines_to_exclude: null,
  pandas_read_csv: null,
  timestamp_columns: [],
  comment: [],
  header: null,
  timezone: null,
  encoding: null,
});

const isLoading = ref(false);

const initialFormData = ref<CsvParserCreate>(normalizeFormData(formData.value));
const isSaving = ref(false);

const hasUnsavedChanges = computed(() => {
  return (
    JSON.stringify(normalizeFormData(formData.value)) !== JSON.stringify(initialFormData.value)
  );
});

useUnsavedChanges(() => hasUnsavedChanges.value && !isSaving.value);

async function save() {
  try {
    const data: CsvParserCreate = normalizeFormData(formData.value);

    isLoading.value = true;
    isSaving.value = true;

    const result = await csvParserStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    await router.push(`/parser/csv/${result.id}`);
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
      message: 'Failed to create parser',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}

function normalizeFormData(data: CsvParserCreate): CsvParserCreate {
  return {
    permission_group_id: data.permission_group_id,
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
    comment: [...(data.comment || [])],
    header: data.header !== null && data.header !== undefined ? data.header : null,
    timezone: data.timezone || null,
    encoding: data.encoding || null,
  };
}
</script>

<style scoped></style>
