<template>
  <ingest-form-external-api-uba
    title="Copy External Api Ingest"
    :is-loading="isLoading"
    :backRoute="detailRoute"
    :item-permission-group="itemPermissionGroup"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import type { IngestExternalApiUbaCreate } from 'src/services/ingest_external_api_uba/types';
import { useIngestExternalApiUbaStore } from 'stores/ingestExternalApiUbaStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiUba from 'components/IngestFormExternalApiUba.vue';

// Composition API
const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const ubaStore = useIngestExternalApiUbaStore();

// Reactive data
const isLoading = ref(false);
const formData = ref<IngestExternalApiUbaCreate>({
  name: '',
  permission_group_id: null,
  description: '',
  station_id: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
});
const itemPermissionGroup = ref<PermissionGroup | null>(null);

// Load existing data when component mounts
onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await ubaStore.dispatchGetOne(id);
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        station_id: data.station_id,
        sync_enabled: data.sync_enabled,
        sync_interval_in_minutes: data.sync_interval_in_minutes,
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
    return `/ingest/external-api/uba/${id}`;
  }
  return '';
});

// Save changes
async function save() {
  if (!route.params.id) return;

  try {
    const data: IngestExternalApiUbaCreate = {
      name: formData.value.name,
      description: formData.value.description,
      permission_group_id: formData.value.permission_group_id,
      station_id: formData.value.station_id,
      sync_enabled: formData.value.sync_enabled,
      sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    };

    isLoading.value = true;

    const result = await ubaStore.dispatchCreate(data);

    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to detail
    await router.push(`/ingest/external-api/uba/${result.id}`);
  } catch (error) {
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    const errorCaption = error?.response?.data?.detail || '';

    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to create Ingest',
      progress: true,
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
