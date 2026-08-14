<template>
  <ingest-form-external-api-t-systems
    title="Copy External Api Ingest"
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
import type { IngestExternalApiTSystemsCreate } from 'src/services/ingest_external_api_tsystems/types';
import { useIngestExternalApiTSystemsStore } from 'stores/ingestExternalApiTSystemsStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiTSystems from 'components/IngestFormExternalApiTSystems.vue';

const tsystemsStore = useIngestExternalApiTSystemsStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestExternalApiTSystemsCreate>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  group: null,
  station_id: null,
  tsystems_username: null,
  tsystems_password: null,
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
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        sync_enabled: data.sync_enabled,
        sync_interval_in_minutes: data.sync_interval_in_minutes,
        group: data.group,
        station_id: data.station_id,
        tsystems_username: null,
        tsystems_password: null,
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
  const data: IngestExternalApiTSystemsCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    group: formData.value.group,
    station_id: formData.value.station_id,
    tsystems_username: formData.value.tsystems_username,
    tsystems_password: formData.value.tsystems_password,
  };
  try {
    isLoading.value = true;
    const result = await tsystemsStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to list
    await router.push(`/ingest/external-api/tsystems/${result.id}`);
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
