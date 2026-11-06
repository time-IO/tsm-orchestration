<template>
  <ingest-form-external-api-zentra
    title="Edit External Api Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :item-permission-group="itemPermissionGroup"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import type { IngestExternalApiZentraUpdate } from '@/services/ingest_external_api_zentra/types';
import { useIngestExternalApiZentraStore } from '@/stores/ingestExternalApiZentraStore';
import type { PermissionGroup } from '@/services/permission_group/types';
import IngestFormExternalApiZentra from '@/components/IngestFormExternalApiZentra.vue';
import { useUnsavedChanges } from '@/composables/useUnsavedChanges';

// Composition API
const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const zenStore = useIngestExternalApiZentraStore();

// Reactive data
const isLoading = ref(false);
const formData = ref<Partial<IngestExternalApiZentraUpdate>>({
  name: '',
  permission_group_id: null,
  description: '',
  device_sn: '',
  period_in_minutes: null,
  units: 'metric',
  sync_enabled: false,
  sync_interval_in_minutes: null,
  api_key: '',
});
const itemPermissionGroup = ref<PermissionGroup | null>(null);

// Load existing data when component mounts
onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await zenStore.dispatchGetOne(id);
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: data.name || '',
        permission_group_id: data.permission_group_id,
        description: data.description,
        device_sn: data.device_sn,
        period_in_minutes: data.period_in_minutes,
        units: data.units,
        sync_enabled: data.sync_enabled,
        sync_interval_in_minutes: data.sync_interval_in_minutes,
        api_key: data.api_key,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load ingest data',
      });
      await router.push('/ingest');
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/external-api/zentra/${id}`;
  }
  return '';
});

// Save changes
async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);
    const data: IngestExternalApiZentraUpdate = {
      name: formData.value.name || '',
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || '',
      device_sn: formData.value.device_sn || '',
      period_in_minutes: formData.value.period_in_minutes || null,
      units: formData.value.units || null,
      sync_enabled: formData.value.sync_enabled || false,
      sync_interval_in_minutes: formData.value.sync_interval_in_minutes || null,
      api_key: formData.value.api_key || '',
    };

    isLoading.value = true;

    await zenStore.dispatchUpdate(id, data);

    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Updated successfully',
    });
    savedForm.value = { ...formData.value };
    // Navigate back to detail
    await router.push(detailRoute.value);
  } catch (error) {
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    const errorCaption = error?.response?.data?.detail || '';

    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to update ingest',
      progress: true,
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
