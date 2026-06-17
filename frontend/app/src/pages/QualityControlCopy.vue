<template>
  <qc-setting-form
    title="Copy QC Setting"
    :is-loading="isLoading"
    :back-url="detailRoute"
    :item-permission-group="itemPermissionGroup"
    v-model="formData"
    @save="save"
  />
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import type { QualityControlSettingCreate } from 'src/services/quality_control_setting/types';
import { useQualityControlSettingStore } from 'stores/qualityControlSettingStore';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import QcSettingForm from 'components/QcSettingForm.vue';
import type { PermissionGroup } from 'src/services/permission_group/types';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const qualityControlSettingStore = useQualityControlSettingStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const isLoading = ref(false);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

const formData = ref<QualityControlSettingCreate>({
  name: null,
  context_window: null,
  is_active: true,
  description: null,
  permission_group_id: null,
  quality_control_functions: [],
});
onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await qualityControlSettingStore.dispatchGetOne(id);

      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: `${data.name} - Copy`,
        context_window: data.context_window,
        is_active: data.is_active,
        description: data.description,
        permission_group_id: data.permission_group_id,
        quality_control_functions: data.quality_control_functions,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load quality control setting',
      });
      await router.push('/parser');
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/quality-control/${id}`;
  }
  return '';
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
    savedForm.value = { ...formData.value };
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

const savedForm = ref({ ...formData.value });
useUnsavedChanges(() => JSON.stringify(formData.value) !== JSON.stringify(savedForm.value));
</script>

<style scoped></style>
