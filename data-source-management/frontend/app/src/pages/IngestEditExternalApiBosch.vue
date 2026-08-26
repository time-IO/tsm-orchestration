<template>
  <ingest-form-external-api-bosch
    title="Edit External Api Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :item-permission-group="itemPermissionGroup"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { useIngestExternalApiBoschStore } from 'stores/ingestExternalApiBoschStore';
import type { IngestExternalApiBoschUpdate } from 'src/services/ingest_external_api_bosch/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiBosch from 'components/IngestFormExternalApiBosch.vue';

const boschStore = useIngestExternalApiBoschStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<Partial<IngestExternalApiBoschUpdate>>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  endpoint: null,
  sensor_id: null,
  bosch_username: null,
  bosch_password: null,
  period_in_minutes: null,
});

const isLoading = ref(false);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await boschStore.dispatchGetOne(id);
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: data.name || '',
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        sync_enabled: data.sync_enabled || false,
        sync_interval_in_minutes: data.sync_interval_in_minutes || null,
        endpoint: data.endpoint || null,
        sensor_id: data.sensor_id || null,
        bosch_username: data.bosch_username || null,
        bosch_password: data.bosch_password || null,
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
    return `/ingest/external-api/bosch/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestExternalApiBoschUpdate = {
      name: formData.value.name || '',
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || null,
      sync_enabled: formData.value.sync_enabled || false,
      sync_interval_in_minutes: formData.value.sync_interval_in_minutes || null,
      endpoint: formData.value.endpoint || null,
      sensor_id: formData.value.sensor_id || null,
      bosch_username: formData.value.bosch_username || null,
      bosch_password: formData.value.bosch_password || null,
      period_in_minutes: formData.value.period_in_minutes || null,
    };

    isLoading.value = true;
    await boschStore.dispatchUpdate(id, data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to list
    await router.push(detailRoute.value);
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
      message: 'Failed to update ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
