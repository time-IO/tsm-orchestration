<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <h6 class="q-mt-none">Palas MyAtmosphere Device Measurements</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>
    <div class="text-caption text-grey">
      For more information on MyAtmosphere API properties, visit the API documentation
      <a href="https://api.my-atmosphere.cloud/swagger/index.html" target="_blank">here</a>.
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
            :disable="disablePermissionGroup"
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
            v-model.number="formData.customer_id"
            label="Customer ID *"
            type="number"
            hint="MyAtmosphere customer (AQ network) the device is assigned to"
            :rules="[rules.REQUIRED, rules.INTEGER, ruleFactories.MIN(1)]"
          />

          <q-input
            filled
            v-model="formData.serial_number"
            label="Device Serial Number *"
            hint="Palas device serial number, e.g. 22935"
            :rules="[(val) => !!val || 'Serial number is required']"
          />
          <q-separator class="q-my-lg" />
          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.period_in_minutes"
            label="Period (in minutes) *"
            type="number"
            hint="Determines the time window fetched per sync."
            :rules="[rules.REQUIRED, rules.INTEGER, ruleFactories.MIN(1)]"
          >
            <template #append>
              <help-button termHelp="period" />
            </template>
          </q-input>
          <q-separator class="q-my-lg" />
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.api_key"
            label="API Key *"
            :type="isPwd ? 'password' : 'text'"
            :rules="[(val) => !!val || 'Key is required']"
          >
            <template v-slot:append>
              <q-icon
                :name="isPwd ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="isPwd = !isPwd"
              />
            </template>
          </q-input>

          <q-separator class="q-my-lg" />
          <!-- Sync Settings -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">Synchronization Settings</div>

            <q-toggle
              v-model="formData.sync_enabled"
              label="Enable Sync"
              color="primary"
              size="md"
            />

            <div class="q-mt-md">
              <q-input
                filled
                v-model.number="formData.sync_interval_in_minutes"
                label="Sync Interval (in minutes) *"
                type="number"
                :rules="[rules.REQUIRED, rules.INTEGER, ruleFactories.MIN(10)]"
              >
                <template #append>
                  <help-button termHelp="sync_interval" />
                </template>
              </q-input>
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
  IngestExternalApiMyAtmosphereCreate,
  IngestExternalApiMyAtmosphereUpdate,
} from '@/services/ingest_external_api_myatmosphere/types';
import type { PermissionGroup } from '@/services/permission_group/types';
import HelpButton from '@/components/HelpButton.vue';
import { ref } from 'vue';
import { ruleFactories, rules } from '@/utils/validation/rules';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
  disablePermissionGroup?: boolean;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<
  IngestExternalApiMyAtmosphereCreate | IngestExternalApiMyAtmosphereUpdate
>({
  default: () => ({
    name: '',
    permission_group_id: null,
    description: null,
    customer_id: null,
    serial_number: '',
    period_in_minutes: null,
    sync_enabled: false,
    sync_interval_in_minutes: null,
    api_key: '',
  }),
});

const isPwd = ref(true);
</script>
