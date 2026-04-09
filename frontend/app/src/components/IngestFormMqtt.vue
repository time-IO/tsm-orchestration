<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>

    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="$emit('save')" class="q-gutter-md">
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
          <mqtt-parser-select v-model="formData.mqtt_parser_id" />
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
import MqttParserSelect from 'components/MqttParserSelect.vue';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import type { IngestMqttCreate, IngestMqttUpdate } from 'src/services/ingest_mqtt/types';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<IngestMqttCreate | IngestMqttUpdate>({
  default: {
    name: null,
    permission_group_id: null,
    description: null,
    topic: null,
    uri: null,
    mqtt_parser_id: null,
  },
});
</script>

<style scoped></style>
