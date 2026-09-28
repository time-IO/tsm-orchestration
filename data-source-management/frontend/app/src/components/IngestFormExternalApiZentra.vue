<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <h6 class="q-mt-none">Zentra</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>
    <div class="text-caption text-grey">
      For more information on Zentra API properties, visit the API documentation
      <a href="https://docs.zentracloud.io/l/en/article/st68yxb51l-api-v-3-0-eu" target="_blank">here</a
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
            hint="Enter a descriptive name for this ingest"
            :rules="[
              (val) => !!val || 'Name is required',
              (val) => val.length <= 80 || 'Maximum 80 characters',
            ]"
          />

          <permission-group-select
            v-model="formData.permission_group_id"
            :preselected-item="itemPermissionGroup"
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
            v-model="formData.device_sn"
            label="Device Serial Number *"
            hint="Zentra device identifier"
            :rules="[(val) => !!val || 'Device ID is required']"
          />
          <q-separator class="q-my-lg" />

          <div class="q-mb-md">
            <q-btn-toggle
              v-model="formData.units"
              :options="[
                { label: 'Metric', value: 'metric', icon: 'mdi-weight-kilogram' },
                { label: 'Imperial', value: 'imperial', icon: 'mdi-weight-pound' },
              ]"
              unelevated
              spread
              toggle-color="blue-grey-5"
              color="grey-3"
              text-color="grey-7"
              toggle-text-color="white"
              class="unit-toggle"
            />
            <div class="text-caption q-field__bottom q-mb-sm">Unit system for measurements</div>
          </div>
          <q-separator class="q-my-lg" />
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
          <q-separator class="q-my-lg" />
          <q-separator class="q-my-lg" />
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.api_key"
            label="API-Key *"
            :rules="[(val) => !!val || 'Key is required']"
          />

          <q-separator class="q-my-lg" />
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
import PermissionGroupSelect from '@/components/PermissionGroupSelect.vue';
import type {
  IngestExternalApiZentraCreate,
  IngestExternalApiZentraUpdate,
} from '@/services/ingest_external_api_zentra/types';
import type { PermissionGroup } from '@/services/permission_group/types';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<IngestExternalApiZentraCreate | IngestExternalApiZentraUpdate>({
  default: () => ({
    name: '',
    permission_group_id: null,
    description: null,
    device_sn: '',
    period_in_minutes: null,
    units: 'metric',
    sync_enabled: false,
    sync_interval_in_minutes: null,
    api_key: '',
  }),
});
</script>

<style scoped>
.unit-toggle {
  width: 50%;
}
</style>
