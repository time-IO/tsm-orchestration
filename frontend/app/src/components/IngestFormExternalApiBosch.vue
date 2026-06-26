<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <h6 class="q-mt-none">Bosch IoT</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>
    <div class="text-caption text-grey">
      For more information on Bosch IoT Insights API properties, visit the
      <a
        href="https://bosch-iot-insights.com/ui/pages/api/mongodb-query/latest"
        target="_blank"
        class="text-primary"
        >API documentation</a
      >.
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
            filled
            class="q-mb-md"
            v-model="formData.endpoint"
            label="Endpoint *"
            :rules="[(val) => !!val || 'Endpoint is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.sensor_id"
            label="Sensor-ID *"
            :rules="[(val) => !!val || 'Sensor-ID is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.bosch_username"
            label="Username *"
            :rules="[(val) => !!val || 'Username is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.bosch_password"
            label="Password *"
            :type="isPwd ? 'password' : 'text'"
            :rules="[(val) => !!val || 'Password is required']"
          >
            <template v-slot:append>
              <q-icon
                :name="isPwd ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="isPwd = !isPwd"
              />
            </template>
          </q-input>

          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.period_in_minutes"
            label="Period (in minutes) *"
            :rules="[
              (val) => !!val || 'Period is required',
              (val) =>
                (val !== null && val !== '' && val > 0) || 'Interval must be a positive number',
            ]"
          />

          <!-- Sync Settings -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">Synchronization Settings</div>

            <q-toggle
              v-model="formData.sync_enabled"
              label="Enable File Server Sync"
              color="primary"
              size="md"
            />

            <div class="q-mt-md">
              <q-input
                filled
                v-model.number="formData.sync_interval_in_minutes"
                label="Sync Interval (in minutes) *"
                type="number"
                :rules="[
                  (val) => !!val || 'Sync intervall is required',
                  (val) =>
                    (val !== null && val !== '' && val > 0) || 'Interval must be a positive number',
                ]"
              />
            </div>
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
import type {
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschUpdate,
} from 'src/services/ingest_external_api_bosch/types';
import { ref } from 'vue';
import type { PermissionGroup } from 'src/services/permission_group/types';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
}>();

defineEmits<{
  save: [];
}>();
const formData = defineModel<IngestExternalApiBoschCreate | IngestExternalApiBoschUpdate>({
  default: {
    name: '',
    permission_group_id: null,
    description: null,
    sync_enabled: false,
    sync_interval_in_minutes: null,
    endpoint: null,
    sensor_id: null,
    bosch_username: null,
    bosch_password: null,
    period_in_minutes: null,
  },
});

const isPwd = ref(true);
</script>

<style scoped></style>
