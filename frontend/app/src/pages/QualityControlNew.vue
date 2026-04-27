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
import type {
  QualityControlSettingCreate,
} from 'src/services/quality_control_setting/types';
import { useQualityControlSettingStore } from 'stores/qualityControlSettingStore';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import QcSettingForm from 'components/QcSettingForm.vue';

const qualityControlSettingStore = useQualityControlSettingStore();
const $q = useQuasar();
const router = useRouter();

const isLoading = ref(false);

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
    await router.push(`/quality-control/${result.id}`);
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
      message: 'Failed to create quality control setting',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
