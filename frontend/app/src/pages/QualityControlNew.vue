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
import { ref } from 'vue';
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
const hasUnsavedChanges = ref(true);

useUnsavedChanges(hasUnsavedChanges.value);

const formData = ref<QualityControlSettingCreate>({
  name: null,
  context_window: null,
  is_active: true,
  description: null,
  permission_group_id: null,
  quality_control_functions: [],
});

async function save() {
  const data: QualityControlSettingCreate = {
    name: formData.value.name,
    is_active: formData.value.is_active,
    context_window: formData.value.context_window,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    quality_control_functions: formData.value.quality_control_functions,
  };
  try {
    isLoading.value = true;
    const result = await qualityControlSettingStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    hasUnsavedChanges.value = false;

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
</script>

<style scoped></style>
