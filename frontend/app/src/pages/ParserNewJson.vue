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
import type { JsonParserCreate } from 'src/services/parser_json/types';
import { useJsonParserStore } from 'stores/parserJsonStore';
import ParserFormJson from 'components/ParserFormJson.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const jsonParserStore = useJsonParserStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<JsonParserCreate>({
  name: '',
  permission_group_id: null,
  description: null,
  timestamp_keys: [],
  comment: null,
  timezone: null,
});

const isLoading = ref(false);

const initialFormData = ref<JsonParserCreate>(normalizeFormData(formData.value));
const isSaving = ref(false);

const hasUnsavedChanges = computed(() => {
  return (
    JSON.stringify(normalizeFormData(formData.value)) !== JSON.stringify(initialFormData.value)
  );
});

useUnsavedChanges(() => hasUnsavedChanges.value && !isSaving.value);

async function save() {
  try {
    const data: JsonParserCreate = normalizeFormData(formData.value);

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

function normalizeFormData(data: JsonParserCreate): JsonParserCreate {
  return {
    permission_group_id: data.permission_group_id,
    name: data.name || '',
    description: data.description || null,
    timestamp_keys: (data.timestamp_keys || []).map((timestampKey) => ({
      key: timestampKey.key,
      format: timestampKey.format,
    })),
    comment: data.comment || null,
    timezone: data.timezone || null,
  };
}
</script>

<style scoped></style>
