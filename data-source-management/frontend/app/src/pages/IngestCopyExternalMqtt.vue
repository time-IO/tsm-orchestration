<template>
  <ingest-form-external-mqtt
    title="Copy External MQTT Ingest"
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
import type { IngestExternalMqttCreate } from 'src/services/ingest_external_mqtt/types';
import { useIngestExternalMqttStore } from 'stores/ingestExternalMqttStore';
import type { PermissionGroup } from 'src/services/permission_group/types';
import IngestFormExternalMqtt from 'components/IngestFormExternalMqtt.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const ingestExternalMqttStore = useIngestExternalMqttStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestExternalMqttCreate>({
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
  enabled: false,
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
        permission_group_id: data.permission_group_id,
        name: `${data.name} - Copy`,
        description: data.description,
        parser_id: data.parser_id,
        external_mqtt_address: data.external_mqtt_address,
        external_mqtt_port: data.external_mqtt_port,
        external_mqtt_topic: data.external_mqtt_topic,
        external_mqtt_username: null,
        external_mqtt_password: null,
        external_mqtt_ca_cert: null,
        external_mqtt_client_cert: null,
        external_mqtt_client_key: null,
        enabled: data.enabled,
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
  const data: IngestExternalMqttCreate = {
    permission_group_id: formData.value.permission_group_id,
    name: formData.value.name,
    description: formData.value.description,
    parser_id: formData.value.parser_id,
    external_mqtt_address: formData.value.external_mqtt_address,
    external_mqtt_port: formData.value.external_mqtt_port,
    external_mqtt_topic: formData.value.external_mqtt_topic,
    external_mqtt_username: formData.value.external_mqtt_username,
    external_mqtt_password: formData.value.external_mqtt_password,
    external_mqtt_ca_cert: formData.value.external_mqtt_ca_cert,
    external_mqtt_client_cert: formData.value.external_mqtt_client_cert,
    external_mqtt_client_key: formData.value.external_mqtt_client_key,
    enabled: formData.value.enabled,
  };
  try {
    isLoading.value = true;
    const result = await ingestExternalMqttStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });
    savedForm.value = { ...formData.value };
    // Navigate to detail
    await router.push(`/ingest/external-mqtt/${result.id}`);
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
      message: 'Failed to create Ingest',
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
