<template>
  <ingest-form-external-api-t-systems
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
import type { IngestExternalApiTSystemsUpdate } from 'src/services/ingest_external_api_tsystems/types';
import { useIngestExternalApiTSystemsStore } from 'stores/ingestExternalApiTSystemsStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiTSystems from 'components/IngestFormExternalApiTSystems.vue';

const tsystemsStore = useIngestExternalApiTSystemsStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<Partial<IngestExternalApiTSystemsUpdate>>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  group: null,
  station_id: null,
  tsystems_username: null,
  tsystems_password: null,
  sync_interval_in_minutes: null,
});

const isLoading = ref(false);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await tsystemsStore.dispatchGetOne(id);
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: data.name || null,
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        sync_enabled: data.sync_enabled || false,
        group: data.group || null,
        station_id: data.station_id || null,
        tsystems_username: data.tsystems_username || null,
        tsystems_password: data.tsystems_password || null,
        sync_interval_in_minutes: 60,
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
    return `/ingest/external-api/tsystems/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestExternalApiTSystemsUpdate = {
      name: formData.value.name || null,
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || null,
      sync_enabled: formData.value.sync_enabled || false,
      group: formData.value.group || null,
      station_id: formData.value.station_id || null,
      tsystems_username: formData.value.tsystems_username || null,
      tsystems_password: formData.value.tsystems_password || null,
    };

    isLoading.value = true;
    await tsystemsStore.dispatchUpdate(id, data);
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
