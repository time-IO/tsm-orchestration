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

const initialFormData = ref<QualityControlSettingCreate | null>(null);
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
      const data = await qualityControlSettingStore.dispatchGetOne(id);

      itemPermissionGroup.value = data.permission_group;

      data.name = `${data.name} - Copy`;

      const loadedData = normalizeFormData(data);

      formData.value = loadedData;
      initialFormData.value = structuredClone(loadedData);
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load Quality Control Setting',
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
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    const detail = error?.response?.data?.detail;
    let errorCaption = '';

    if (Array.isArray(detail)) {
      errorCaption = detail.map((item) => item.msg).join('\n');
    } else if (detail && typeof detail === 'object') {
      errorCaption = detail.errors?.join('\n') || detail.message || '';
    } else {
      errorCaption = detail || '';
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
      message: 'Failed to create Quality Control Setting',
      caption: errorCaption,
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
