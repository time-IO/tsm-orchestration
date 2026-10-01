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
import { computed, ref, toRaw } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useCsvParserStore } from '@/stores/parserCsvStore';
import ParserFormCsv from '@/components/ParserFormCsv.vue';
import { useUnsavedChanges } from '@/composables/useUnsavedChanges';
import { formToApi, type CsvParserFormData } from '@/utils/parser_csv_utils';

const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<CsvParserFormData>({
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

const initialFormData = ref<CsvParserFormData>(
  structuredClone(toRaw(formData.value)),
);
const isSaving = ref(false);

const hasUnsavedChanges = computed(() => {
  return (
    JSON.stringify(formData.value) !==
    JSON.stringify(initialFormData.value)
  );
});

useUnsavedChanges(() => hasUnsavedChanges.value && !isSaving.value);

async function save() {
  try {
    const data = formToApi(formData.value, true);

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
</script>

<style scoped></style>
