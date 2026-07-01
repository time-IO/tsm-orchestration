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
            hint="Enter a descriptive name for this Ingest"
            :rules="[
              (val) => !!val || 'Name is required',
              (val) => val.length <= 80 || 'Maximum 80 characters',
            ]"
          />

          <permission-group-select
            v-model="formData.permission_group_id"
            :preselected-item="itemPermissionGroup"
            :rules="[(val) => !!val || 'Permission Group is required']"
          />

          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this Ingest Configuration"
          />

          <q-input
            v-if="allowUsernameInput"
            v-model="usernameModel"
            filled
            class="q-mb-md"
            label="MQTT Username"
            hint="Optional. Leave empty to auto-generate. Minimum 8 characters. Allowed characters: lowercase letters, numbers, hyphens."
            :rules="[
              (val) => !val || val.length >= 8 || 'Must be at least 8 characters long',
              (val) => !val || /^[a-z0-9-]+$/.test(val) || 'Only lowercase letters, numbers, and hyphens are allowed',
            ]"
          />

          <mqtt-parser-select v-model="formData.parser_id" :preselected-item-id="itemParserId" />
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
import { computed } from 'vue';
import MqttParserSelect from 'components/MqttParserSelect.vue';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import type { IngestMqttCreate, IngestMqttUpdate } from 'src/services/ingest_mqtt/types';
import type { PermissionGroup } from 'src/services/permission_group/types';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
  itemParserId?: number | null | undefined;
  allowUsernameInput?: boolean;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<IngestMqttCreate | IngestMqttUpdate>({
  default: {
    name: null,
    permission_group_id: null,
    description: null,
    parser_id: null,
  },
});

const usernameModel = computed({
  get: () => ('username' in formData.value ? formData.value.username : null),
  set: (value: string | null) => {
    if ('username' in formData.value) {
      formData.value.username = value;
    }
  },
});
</script>

<style scoped></style>
