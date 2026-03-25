<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New MQTT Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new" />
      </div>
    </div>

    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="save" class="q-gutter-md">
          <!-- Name Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this ingest"
            :rules="[(val) => !!val || 'Name is required']"
          />

          <permission-group-select
            v-model="formData.permission_group_id"
            :rules="[(val) => !!val || 'Permission group is required']"
          />

          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this ingest configuration"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.uri"
            label="Broker URI *"
            :rules="[(val) => !!val || 'Broker URI is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.topic"
            label="Topic *"
            :rules="[(val) => !!val || 'Topic is required']"
          />
          <mqtt-parser-select
            v-model="formData.mqtt_parser_id"
          />
          <!-- Action Buttons -->
          <div class="row q-mt-lg">
            <q-space />
            <div class="col-6">
              <q-btn
                unelevated
                color="green"
                type="submit"
                :loading="isLoading"
                label="Save"
                class="full-width"
              />
            </div>
            <q-space />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import type { IngestMqttCreate } from 'src/services/ingest_mqtt/types';
import { useIngestMqttStore } from 'stores/ingestMqttStore';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import MqttParserSelect from 'components/MqttParserSelect.vue';

const mqttStore = useIngestMqttStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestMqttCreate>({
  name: null,
  permission_group_id: null,
  description: null,
  topic: null,
  uri: null,
  mqtt_parser_id: null,
});

const isLoading = ref(false);

async function save() {
  const data: IngestMqttCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    topic: formData.value.topic,
    uri: formData.value.uri,
    mqtt_parser_id: formData.value.mqtt_parser_id,
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

</script>

<style scoped></style>
