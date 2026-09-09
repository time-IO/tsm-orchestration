<template>
  <parser-form-json
    title="Edit JSON Parser"
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
import type { JsonParserUpdate } from 'src/services/parser_json/types';
import { useJsonParserStore } from 'stores/parserJsonStore';
import ParserFormJson from 'components/ParserFormJson.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';
import type { JsonParserFormData } from 'src/services/parser_json/formTypes';

const jsonParserStore = useJsonParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<JsonParserFormData>({
  name: '',
  description: null,
  timestamp_keys: [],
  comment: null,
  measurement_key: null,
  timezone: null,
  excluded_keys: [],
});
const permissionGroupId = ref<number | null>(null);

const isLoading = ref(false);
const isSaving = ref(false);

const initialFormData = ref<JsonParserFormData | null>(null);

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
    return `/parser/json/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: JsonParserUpdate = normalizeFormData(formData.value);

    isLoading.value = true;
    isSaving.value = true;

    await jsonParserStore.dispatchUpdate(id, data);

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

function normalizeFormData(data: JsonParserUpdate): JsonParserFormData {
  return {
    name: data.name || '',
    description: data.description || null,
    timestamp_keys: (data.timestamp_keys || []).map((timestampKey) => ({
      key: timestampKey.key,
      format: timestampKey.format,
    })),
    comment: data.comment || null,
    measurement_key: data.measurement_key || null,
    excluded_keys: data.excluded_keys || [],
    timezone: data.timezone || null,
  };
}
</script>

<style scoped></style>
