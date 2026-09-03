<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <div class="row">
      <div class="col">
        <q-btn label="Back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
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

          <!-- Parser Selection -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">Parser Settings</div>

            <div class="q-mt-md">
              <parser-select
                class="q-mb-md"
                :disable="!formData.permission_group_id"
                v-model="formData.parser_id"
                :permission_group_id="formData.permission_group_id!"
                :preselected_item_id="itemParserId"
              />
            </div>
          </q-card-section>

          <!-- External MQTT Settings -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">External MQTT Settings</div>

            <div class="q-mt-md">
              <q-input
                filled
                class="q-mb-md"
                v-model="formData.external_mqtt_address"
                label="MQTT Broker Address *"
                :rules="[(val) => !!val || 'MQTT Broker Address is required']"
              >
                <template #append>
                  <help-button
                    titleHelp="MQTT Broker Address"
                    textHelp="The hostname or IP address of the external MQTT broker."
                  />
                </template>
              </q-input>

              <q-input
                filled
                class="q-mb-md"
                v-model.number="formData.external_mqtt_port"
                label="MQTT Broker Port *"
                type="number"
                :rules="[
                  (val) => !!val || 'MQTT Broker Port is required',
                  (val) => val > 0 && val <= 65535 || 'Port must be between 1 and 65535',
                ]"
              >
                <template #append>
                  <help-button
                    titleHelp="MQTT Broker Port"
                    textHelp="The port number of the external MQTT broker (default: 1883 for non-TLS, 8883 for TLS)."
                  />
                </template>
              </q-input>

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.external_mqtt_topic"
                label="MQTT Topic *"
                :rules="[(val) => !!val || 'MQTT Topic is required']"
              >
                <template #append>
                  <help-button
                    titleHelp="MQTT Topic"
                    textHelp="The MQTT topic to subscribe to for receiving messages."
                  />
                </template>
              </q-input>

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.external_mqtt_username"
                label="Username"
              />

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.external_mqtt_password"
                label="Password"
                :type="isPwd ? 'password' : 'text'"
              >
                <template v-slot:append>
                  <q-icon
                    :name="isPwd ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer"
                    @click="isPwd = !isPwd"
                  />
                </template>
              </q-input>
            </div>
          </q-card-section>

          <!-- TLS/SSL Certificates -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">TLS/SSL Certificates (Optional)</div>

            <div class="q-mt-md">
              <q-input
                filled
                class="q-mb-md"
                v-model="formData.external_mqtt_ca_cert"
                label="CA Certificate"
                type="textarea"
                rows="4"
              >
                <template #append>
                  <help-button
                    titleHelp="CA Certificate"
                    textHelp="The CA (Certificate Authority) certificate used to verify the MQTT broker's certificate."
                  />
                </template>
              </q-input>

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.external_mqtt_client_cert"
                label="Client Certificate"
                type="textarea"
                rows="4"
              >
                <template #append>
                  <help-button
                    titleHelp="Client Certificate"
                    textHelp="The client certificate for TLS authentication with the MQTT broker."
                  />
                </template>
              </q-input>

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.external_mqtt_client_key"
                label="Client Key"
                type="textarea"
                rows="4"
              >
                <template #append>
                  <help-button
                    titleHelp="Client Key"
                    textHelp="The private key corresponding to the client certificate."
                  />
                </template>
              </q-input>
            </div>
          </q-card-section>

          <!-- Enable Toggle -->
          <q-card-section class="q-pa-none">
            <q-toggle
              v-model="formData.enabled"
              label="Enable External MQTT Ingest"
              color="primary"
              size="md"
            />
          </q-card-section>

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
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import ParserSelect from 'components/ParserSelect.vue';
import HelpButton from 'components/HelpButton.vue';
import { ref } from 'vue';
import type {
  IngestExternalMqttCreate,
  IngestExternalMqttUpdate,
} from 'src/services/ingest_external_mqtt/types';
import type { PermissionGroup } from 'src/services/permission_group/types';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
  itemParserId?: number | null | undefined;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<IngestExternalMqttCreate | IngestExternalMqttUpdate>({
  default: {
    permission_group_id: null,
    name: null,
    description: null,
    parser_id: null,
    external_mqtt_address: null,
    external_mqtt_port: null,
    external_mqtt_username: null,
    external_mqtt_password: null,
    external_mqtt_ca_cert: null,
    external_mqtt_client_cert: null,
    external_mqtt_client_key: null,
    external_mqtt_topic: null,
    enabled: false,
  },
});

const isPwd = ref(true);
</script>

<style scoped></style>
