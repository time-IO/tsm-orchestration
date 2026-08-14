<template>
  <ingest-form-external-api-sensoto
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
import type { IngestExternalApiSensotoUpdate } from 'src/services/ingest_external_api_sensoto/types';
import { useIngestExternalApiSensotoStore } from 'stores/ingestExternalApiSensotoStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiSensoto from 'components/IngestFormExternalApiSensoto.vue';

// Composition API
const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const sensStore = useIngestExternalApiSensotoStore();

// Reactive data
const isLoading = ref(false);
const formData = ref<Partial<IngestExternalApiSensotoUpdate>>({
  name: '',
  permission_group_id: null,
  description: '',
  network: '',
  device: '',
  sync_enabled: false,
  sync_interval_in_minutes: null,
  period_in_minutes: null,
});
const itemPermissionGroup = ref<PermissionGroup | null>(null);

// Load existing data when component mounts
onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await sensStore.dispatchGetOne(id);
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: data.name || '',
        permission_group_id: data.permission_group_id || null,
        description: data.description || '',
        network: data.network || '',
        device: data.device || '',
        sync_enabled: data.sync_enabled || false,
        sync_interval_in_minutes: data.sync_interval_in_minutes || null,
        period_in_minutes: data.period_in_minutes || null,
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
    return `/ingest/external-api/sensoto/${id}`;
  }
  return '';
});

// Save changes
async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);
    const data: IngestExternalApiSensotoUpdate = {
      name: formData.value.name || '',
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || '',
      network: formData.value.network || '',
      device: formData.value.device || '',
      sync_enabled: formData.value.sync_enabled || false,
      sync_interval_in_minutes: formData.value.sync_interval_in_minutes || null,
      period_in_minutes: formData.value.period_in_minutes || null,
    };

    isLoading.value = true;

    await sensStore.dispatchUpdate(id, data);

    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Updated successfully',
    });

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
</script>

<style scoped></style>
