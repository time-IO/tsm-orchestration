<template>
  <ingest-form-mqtt
    title="Edit MQTT Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :item-permission-group="itemPermissionGroup"
    :item-parser="itemParser"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { IngestMqttUpdate } from 'src/services/ingest_mqtt/types';
import { useIngestMqttStore } from 'stores/ingestMqttStore';
import type { MqttParser } from 'src/services/mqtt_parser/type';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormMqtt from 'components/IngestFormMqtt.vue';

const mqttStore = useIngestMqttStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestMqttUpdate>({
  name: null,
  permission_group_id: null,
  description: null,
  topic: null,
  uri: null,
  mqtt_parser_id: null,
});

const isLoading = ref(false);
const itemParser = ref<MqttParser | null>(null);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await mqttStore.dispatchGetOne(id);

      itemParser.value = data.mqtt_parser;
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        name: data.name || null,
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        topic: data.topic || null,
        uri: data.uri || null,
        mqtt_parser_id: data.mqtt_parser_id || null,
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
    return `/ingest/mqtt/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestMqttUpdate = {
      name: formData.value.name || null,
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || null,
      topic: formData.value.topic || null,
      uri: formData.value.uri || null,
      mqtt_parser_id: formData.value.mqtt_parser_id || null,
    };

    isLoading.value = true;

    await mqttStore.dispatchUpdate(id, data);

    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate to detail
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
      progress: true,
      message: 'Failed to update ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
