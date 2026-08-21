<template>
  <ingest-form-external-api-dwd
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
import type { IngestExternalApiDwdCreate } from 'src/services/ingest_external_api_dwd/types';
import { useIngestExternalApiDwdStore } from 'stores/ingestExternalApiDwdStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiDwd from 'components/IngestFormExternalApiDwd.vue';

// Composition API
const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const dwdStore = useIngestExternalApiDwdStore();

// Reactive data
const isLoading = ref(false);
const formData = ref<IngestExternalApiDwdCreate>({
  name: '',
  permission_group_id: null,
  description: '',
  station_id: null,
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
      const data = await dwdStore.dispatchGetOne(id);
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        station_id: data.station_id,
        sync_enabled: data.sync_enabled,
        sync_interval_in_minutes: data.sync_interval_in_minutes,
        period_in_minutes: data.period_in_minutes,
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
    return `/ingest/external-api/dwd/${id}`;
  }
  return '';
});

async function save() {
  const data: IngestExternalApiDwdCreate = {
    name: formData.value.name,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    station_id: formData.value.station_id,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    period_in_minutes: formData.value.period_in_minutes,
  };
  try {
    isLoading.value = true;
    const result = await dwdStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to list
    await router.push(`/ingest/external-api/dwd/${result.id}`);
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
      message: 'Failed to create Ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
