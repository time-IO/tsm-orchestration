<template>
  <parser-form-json
    title="New JSON Parser"
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
import { useJsonParserStore } from 'stores/parserJsonStore';
import type { JsonParserCreate } from 'src/services/parser_json/types';
import ParserFormJson from 'components/ParserFormJson.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';
import type { JsonParserFormData } from 'src/services/parser_json/formTypes';

const jsonParserStore = useJsonParserStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<JsonParserFormData>({
  name: '',
  permission_group_id: null,
  description: null,
  timestamp_keys: [],
  comment: null,
  timezone: null,
  measurement_key: null,
  excluded_keys: [],
});

const isLoading = ref(false);

const initialFormData = ref<JsonParserFormData>(normalizeFormData(formData.value));
const isSaving = ref(false);

const hasUnsavedChanges = computed(() => {
  return (
    JSON.stringify(normalizeFormData(formData.value)) !== JSON.stringify(initialFormData.value)
  );
});

useUnsavedChanges(() => hasUnsavedChanges.value && !isSaving.value);

async function save() {
  try {
    const formValues = normalizeFormData(formData.value);
    const data: JsonParserCreate = {
      name: formValues.name ?? '',
      permission_group_id: formValues.permission_group_id ?? null,
      description: formValues.description ?? null,
      comment: formValues.comment ?? null,
      timestamp_keys: formValues.timestamp_keys,
      timezone: formValues.timezone ?? '',
      measurement_key: formValues.measurement_key ?? null,
      excluded_keys: formValues.excluded_keys,
    };
    isLoading.value = true;
    isSaving.value = true;

    const result = await jsonParserStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    await router.push(`/parser/json/${result.id}`);
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

function normalizeFormData(data: JsonParserFormData): JsonParserFormData {
  return {
    permission_group_id: data.permission_group_id ?? null,
    name: data.name || '',
    description: data.description || null,
    timestamp_keys: (data.timestamp_keys || []).map((timestampKey) => ({
      key: timestampKey.key,
      format: timestampKey.format,
    })),
    comment: data.comment || null,
    timezone: data.timezone || null,
    measurement_key: data.measurement_key || null,
    excluded_keys: data.excluded_keys || [],
  };
}
</script>

<style scoped></style>
