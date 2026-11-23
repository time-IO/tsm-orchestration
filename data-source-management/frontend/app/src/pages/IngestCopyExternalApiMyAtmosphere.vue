<template>
  <ingest-form-external-api-myatmosphere
    title="Copy External Api Ingest"
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
import type { IngestExternalApiMyAtmosphereCreate } from '@/services/ingest_external_api_myatmosphere/types';
import { useIngestExternalApiMyAtmosphereStore } from '@/stores/ingestExternalApiMyAtmosphereStore';
import type { PermissionGroup } from '@/services/permission_group/types';
import IngestFormExternalApiMyAtmosphere from '@/components/IngestFormExternalApiMyAtmosphere.vue';
import { useUnsavedChanges } from '@/composables/useUnsavedChanges';

// Composition API
const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const zenStore = useIngestExternalApiMyAtmosphereStore();

// Reactive data
const isLoading = ref(false);
const formData = ref<IngestExternalApiMyAtmosphereCreate>({
  name: '',
  permission_group_id: null,
  description: '',
  customer_id: null,
  serial_number: '',
  period_in_minutes: null,
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
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        customer_id: data.customer_id,
        serial_number: data.serial_number,
        period_in_minutes: data.period_in_minutes,
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
    return `/ingest/external-api/myatmosphere/${id}`;
  }
  return '';
});

async function save() {
  const data: IngestExternalApiMyAtmosphereCreate = {
    name: formData.value.name,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    customer_id: formData.value.customer_id,
    serial_number: formData.value.serial_number,
    period_in_minutes: formData.value.period_in_minutes,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    api_key: formData.value.api_key,
  };
  try {
    isLoading.value = true;
    const result = await zenStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    savedForm.value = { ...formData.value };
    // Navigate back to list
    await router.push(`/ingest/external-api/myatmosphere/${result.id}`);
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
      message: 'Failed to create ingest',
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
