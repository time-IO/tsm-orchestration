<template>
  <ingest-form-mqtt
    title="New MQTT Ingest"
    :is-loading="isLoading"
    back-route="/ingest/new"
    v-model="formData"
    @save="save"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import type { IngestMqttCreate } from 'src/services/ingest_mqtt/types';
import { useIngestMqttStore } from 'stores/ingestMqttStore';
import IngestFormMqtt from 'components/IngestFormMqtt.vue';
import { useUnsavedChanges } from 'src/composables/useUnsavedChanges';

const mqttStore = useIngestMqttStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestMqttCreate>({
  name: null,
  permission_group_id: null,
  description: null,
  parser_id: null,
});

const isLoading = ref(false);

async function save() {
  const data: IngestMqttCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    parser_id: formData.value.parser_id,
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
