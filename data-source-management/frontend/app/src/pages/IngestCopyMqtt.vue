<template>
  <ingest-form-mqtt
    title="Copy MQTT Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :item-permission-group="itemPermissionGroup"
    :item-parser-id="formData.parser_id"
    :allow-username-input="true"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { IngestMqttCreate } from 'src/services/ingest_mqtt/types';
import { useIngestMqttStore } from 'stores/ingestMqttStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormMqtt from 'components/IngestFormMqtt.vue';

const mqttStore = useIngestMqttStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestMqttCreate>({
  name: null,
  permission_group_id: null,
  description: null,
  parser_id: null,
  username: null,
});

const isLoading = ref(false);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await mqttStore.dispatchGetOne(id);

      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: `${data.name} - Copy`,
        permission_group_id: data.permission_group_id,
        description: data.description,
        parser_id: data.parser_id,
        username: null,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load Ingest Data',
      });
      await router.push('/ingest');
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/mqtt/${id}`;
  }
  return '';
});

async function save() {
  const data: IngestMqttCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    parser_id: formData.value.parser_id,
    username: formData.value.username,
  };
  try {
    isLoading.value = true;
    const result = await mqttStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    // Navigate to detail
    await router.push(`/ingest/mqtt/${result.id}`);
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
