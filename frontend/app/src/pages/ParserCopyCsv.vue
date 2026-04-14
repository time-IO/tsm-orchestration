<template>
  <parser-form-csv
    title="Copy CSV Parser"
    :is-loading="isLoading"
    back-route="/parser/new"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { CsvParserCreate } from 'src/services/parser_csv/types';
import { useCsvParserStore } from 'stores/parserCsvStore';
import ParserFormCsv from 'components/ParserFormCsv.vue';

const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<CsvParserCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  delimiter: null,
  headlines_to_exclude: 0,
  footlines_to_exclude: 0,
  pandas_read_csv: null,
  timestamp_columns: [],
  comment: [],
  header: null,
  timezone: null,
  encoding: null,
});

const isLoading = ref(false);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await csvParserStore.dispatchGetOne(id);

      formData.value = {
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        delimiter: data.delimiter,
        headlines_to_exclude: data.headlines_to_exclude,
        footlines_to_exclude: data.footlines_to_exclude,
        pandas_read_csv: data.pandas_read_csv,
        timestamp_columns: data.timestamp_columns,
        header: data.header,
        comment: data.comment,
        timezone: data.timezone,
        encoding: data.encoding,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load parser data',
      });
      await router.push('/parser');
    }
  }
});

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
</script>

<style scoped></style>
