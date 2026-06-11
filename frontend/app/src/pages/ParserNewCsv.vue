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
import { ref } from 'vue';
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

async function save() {
  try {
    const data: CsvParserCreate = {
      permission_group_id: formData.value.permission_group_id,
      name: formData.value.name,
      description: formData.value.description,
      delimiter: formData.value.delimiter,
      headlines_to_exclude:
        formData.value.headlines_to_exclude !== null &&
        formData.value.headlines_to_exclude !== undefined
          ? formData.value.headlines_to_exclude
          : null,
      footlines_to_exclude:
        formData.value.footlines_to_exclude !== null &&
        formData.value.footlines_to_exclude !== undefined
          ? formData.value.footlines_to_exclude
          : null,
      pandas_read_csv: formData.value.pandas_read_csv,
      timestamp_columns: formData.value.timestamp_columns,
      comment: formData.value.comment,
      header: formData.value.header,
      timezone: formData.value.timezone,
      encoding: formData.value.encoding,
    };

    isLoading.value = true;
    const result = await csvParserStore.dispatchCreate(data);
    savedForm.value = { ...formData.value };
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
      progress: true,
      message: 'Failed to create parser',
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
