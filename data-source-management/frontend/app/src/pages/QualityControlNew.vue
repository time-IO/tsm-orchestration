<template>
  <qc-setting-form
    title="New QC Setting"
    :is-loading="isLoading"
    back-url="/quality-control"
    v-model="formData"
    @save="save"
  />
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import type { QualityControlSettingCreate } from 'src/services/quality_control_setting/types';
import { useQualityControlSettingStore } from 'stores/qualityControlSettingStore';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import QcSettingForm from 'components/QcSettingForm.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const qualityControlSettingStore = useQualityControlSettingStore();
const $q = useQuasar();
const router = useRouter();

const isLoading = ref(false);

const formData = ref<QualityControlSettingCreate>({
  name: null,
  context_window: '0',
  is_active: true,
  description: null,
  permission_group_id: null,
  quality_control_functions: [],
});

const initialFormData = ref<QualityControlSettingCreate>(normalizeFormData(formData.value));
const isSaving = ref(false);

const hasUnsavedChanges = computed(() => {
  return (
    JSON.stringify(normalizeFormData(formData.value)) !== JSON.stringify(initialFormData.value)
  );
});

useUnsavedChanges(() => hasUnsavedChanges.value && !isSaving.value);

async function save() {
  const data: QualityControlSettingCreate = normalizeFormData(formData.value);

  try {
    isLoading.value = true;
    isSaving.value = true;

    const result = await qualityControlSettingStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    await router.push(`/quality-control/${result.id}`);
  } catch (error) {
    // @ts-expect-error Axios error shape
    const detail = error?.response?.data?.detail;

    let errorCaption = '';

    if (typeof detail === 'string') {
      errorCaption = detail;
    } else if (Array.isArray(detail)) {
      // FastAPI/Pydantic validation errors:
      // [{ type, loc, msg, input }]
      errorCaption = detail.map((entry) => entry.msg ?? String(entry)).join('\n');
    } else if (detail && typeof detail === 'object') {
      // Custom backend validation errors:
      // { message: string, errors: string[] }
      if (Array.isArray(detail.errors)) {
        errorCaption = detail.errors.join('\n');
      } else if (typeof detail.message === 'string') {
        errorCaption = detail.message;
      } else {
        errorCaption = JSON.stringify(detail);
      }
    }

    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to create Quality Control Setting',
      caption: errorCaption,
      timeout: 0,
      actions: [
        {
          icon: 'close',
          color: 'white',
          round: true,
          handler: () => {},
        },
      ],
    });
  } finally {
    isLoading.value = false;
  }
}

function normalizeFormData(data: QualityControlSettingCreate): QualityControlSettingCreate {
  return {
    name: data.name || null,
    context_window: data.context_window || null,
    is_active: data.is_active || false,
    description: data.description || null,
    permission_group_id: data.permission_group_id || null,
    quality_control_functions: (data.quality_control_functions || []).map((func) => ({
      name: func.name,
      label: func.label,
      quality_control_function_arguments: (func.quality_control_function_arguments || []).map(
        (arg) => ({
          name: arg.name,
          type: arg.type,
          input: {
            value: arg.input.value,
          },
        }),
      ),
    })),
  };
}
</script>

<style scoped></style>
