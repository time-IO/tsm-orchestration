<template>
  <ingest-form-external-api-ttn
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
import { useIngestExternalApiTheThingsNetworkStore } from 'stores/ingestExternalApiTheThingsNetworkStore';
import type { IngestExternalApiTheThingsNetworkCreate } from 'src/services/ingest_external_api_the_things_network/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalApiTtn from 'components/IngestFormExternalApiTtn.vue';

const ttnStore = useIngestExternalApiTheThingsNetworkStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestExternalApiTheThingsNetworkCreate>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  endpoint_uri: null,
  api_key: null,
});

const isLoading = ref(false);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await ttnStore.dispatchGetOne(id);
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        sync_enabled: data.sync_enabled,
        sync_interval_in_minutes: data.sync_interval_in_minutes,
        endpoint_uri: data.endpoint_uri,
        api_key: null,
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
    return `/ingest/external-api/ttn/${id}`;
  }
  return '';
});

async function save() {
  const data: IngestExternalApiTheThingsNetworkCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    endpoint_uri: formData.value.endpoint_uri,
    api_key: formData.value.api_key,
  };
  try {
    isLoading.value = true;
    const result = await ttnStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate back to list
    await router.push(`/ingest/external-api/ttn/${result.id}`);
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
