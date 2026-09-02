<template>
  <parser-form-soilcan
    title="Copy SOILCAN Parser"
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
import type { SoilcanParserCreate } from 'src/services/parser_soilcan/types';
import { useSoilcanParserStore } from 'stores/parserSoilcanStore';
import ParserFormSoilcan from 'components/ParserFormSoilcan.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const soilcanParserStore = useSoilcanParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<SoilcanParserCreate>({
  name: '',
  permission_group_id: null,
  description: null,
  header: false,
  type: '',
});

const isLoading = ref(false);
const isSaving = ref(false);

const initialFormData = ref<SoilcanParserCreate | null>(null);

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
      const data = await soilcanParserStore.dispatchGetOne(id);

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
    return `/parser/soilcan/${id}`;
  }
  return '';
});

async function save() {
  try {
    const data: SoilcanParserCreate = normalizeFormData(formData.value);

    isLoading.value = true;
    isSaving.value = true;

    const result = await soilcanParserStore.dispatchCreate(data);

    await router.push(`/parser/soilcan/${result.id}`);
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

function normalizeFormData(data: SoilcanParserCreate): SoilcanParserCreate {
  return {
    permission_group_id: data.permission_group_id,
    name: data.name || '',
    description: data.description || null,
    header: data.header || false,
    type: data.type || '',
  };
}
</script>

<style scoped></style>
