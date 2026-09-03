<template>
  <ingest-form-external-mqtt
    title="Edit External MQTT Ingest"
    :is-loading="isLoading"
    :back-route="detailRoute"
    :item-permission-group="itemPermissionGroup"
    :item-parser-id="formData.parser_id"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { IngestExternalMqttUpdate } from 'src/services/ingest_external_mqtt/types';
import { useIngestExternalMqttStore } from 'stores/ingestExternalMqttStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalMqtt from 'components/IngestFormExternalMqtt.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const ingestExternalMqttStore = useIngestExternalMqttStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestExternalMqttUpdate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_id: null,
  external_mqtt_address: null,
  external_mqtt_port: null,
  external_mqtt_topic: null,
  external_mqtt_username: null,
  external_mqtt_password: null,
  external_mqtt_ca_cert: null,
  external_mqtt_client_cert: null,
  external_mqtt_client_key: null,
  enabled: null,
});

const isLoading = ref(false);

const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await ingestExternalMqttStore.dispatchGetOne(id);

      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        permission_group_id: data.permission_group_id || null,
        name: data.name || null,
        description: data.description || null,
        parser_id: data.parser_id || null,
        external_mqtt_address: data.external_mqtt_address || null,
        external_mqtt_port: data.external_mqtt_port || null,
        external_mqtt_topic: data.external_mqtt_topic || null,
        external_mqtt_username: data.external_mqtt_username || null,
        external_mqtt_password: data.external_mqtt_password || null,
        external_mqtt_ca_cert: data.external_mqtt_ca_cert || null,
        external_mqtt_client_cert: data.external_mqtt_client_cert || null,
        external_mqtt_client_key: data.external_mqtt_client_key || null,
        enabled: data.enabled || null,
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
    return `/ingest/external-mqtt/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestExternalMqttUpdate = {
      permission_group_id: formData.value.permission_group_id || null,
      name: formData.value.name || null,
      description: formData.value.description || null,
      parser_id: formData.value.parser_id || null,
      external_mqtt_address: formData.value.external_mqtt_address || null,
      external_mqtt_port: formData.value.external_mqtt_port || null,
      external_mqtt_topic: formData.value.external_mqtt_topic || null,
      external_mqtt_username: formData.value.external_mqtt_username || null,
      external_mqtt_password: formData.value.external_mqtt_password || null,
      external_mqtt_ca_cert: formData.value.external_mqtt_ca_cert || null,
      external_mqtt_client_cert: formData.value.external_mqtt_client_cert || null,
      external_mqtt_client_key: formData.value.external_mqtt_client_key || null,
      enabled: formData.value.enabled || null,
    };

    isLoading.value = true;

    await ingestExternalMqttStore.dispatchUpdate(id, data);

    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    savedForm.value = { ...formData.value };
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

const savedForm = ref({ ...formData.value });
useUnsavedChanges(() => JSON.stringify(formData.value) !== JSON.stringify(savedForm.value));
</script>

<style scoped></style>
