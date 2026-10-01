<template>
  <parser-form-csv
    title="Edit CSV Parser"
    :is-loading="isLoading"
    :back-route="detailRoute"
    disable-permission-group
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { useCsvParserStore } from '@/stores/parserCsvStore';
import ParserFormCsv from '@/components/ParserFormCsv.vue';
import { useUnsavedChanges } from '@/composables/useUnsavedChanges';
import {
  apiToForm,
  formToApi,
  type CsvParserFormData,
} from '@/utils/parser_csv_utils';

const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<CsvParserFormData>({
  permission_group_id: null,
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
const isLoading = ref(false);
const isSaving = ref(false);

const initialFormData = ref<CsvParserFormData | null>(null);

const hasUnsavedChanges = computed(() => {
  if (!initialFormData.value) return false;

  return (
    JSON.stringify(formData.value) !==
    JSON.stringify(initialFormData.value)
  );
});

useUnsavedChanges(() => hasUnsavedChanges.value && !isSaving.value);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await csvParserStore.dispatchGetOne(id);

      const loadedData = apiToForm(data);

      formData.value = loadedData;
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

    const data = formToApi(formData.value);

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
</script>

<style scoped></style>
