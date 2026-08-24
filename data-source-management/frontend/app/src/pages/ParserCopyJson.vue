<template>
  <parser-form-json
    title="Copy JSON Parser"
    :is-loading="isLoading"
    :back-route="detailRoute"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type {JsonParserCreate, JsonParserPublic, JsonParserUpdate} from 'src/services/parser_json/types';
import { useJsonParserStore } from 'stores/parserJsonStore';
import ParserFormJson from 'components/ParserFormJson.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';


const jsonParserStore = useJsonParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

type JsonParserFormData = JsonParserUpdate & {
  permission_group_id?: number | null;
  timestamp_keys: JsonParserCreate['timestamp_keys'];
  excluded_keys: string[];
};

const isLoading = ref(false);

const initialFormData = ref<JsonParserUpdate | null>(null);
const isSaving = ref(false);

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
      const data = await jsonParserStore.dispatchGetOne(id);

      data.name = `${data.name} - Copy`;

      const loadedData = normalizeFormData(data);

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
    return `/parser/json/${id}`;
  }
  return '';
});

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

function normalizeFormData(data: JsonParserUpdate): JsonParserUpdate {
  return {
    name: data.name || '',
    description: data.description || null,
    timestamp_keys: data.timestamp_keys || [],
    comment: data.comment || null,
    timezone: data.timezone || null,
    measurement_key: data.measurement_key || null,
    excluded_keys: data.excluded_keys || [],
  };
}
</script>

<style scoped></style>
