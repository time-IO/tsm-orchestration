<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <h6 class="q-mt-none">Sensoto</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>
    <p>
      For more information on Sensoto API properties, visit the API documentation
      <a href="https://sensoto.io/en/documentation/" target="_blank">here</a>.
    </p>
    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="$emit('save')" class="q-gutter-md">
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this ingest"
            :rules="[rules.REQUIRED, ruleFactories.MAX(80)]"
          />

          <permission-group-select
            v-model="formData.permission_group_id"
            :preselected-item="itemPermissionGroup"
            :rules="[rules.REQUIRED]"
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
          <q-separator class="q-my-lg" />

          <div class="text-subtitle1">Organization &amp; access</div>

          <q-input
            filled
            v-model="formData.organization"
            label="Organization *"
            type="text"
            hint="Sensoto organization the network belongs to, e.g. open or valigruen"
            :rules="[rules.REQUIRED]"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.token"
            label="Token (optional)"
            :type="isPwd ? 'password' : 'text'"
            hint="Only needed for protected data. The token must grant access to the organization above."
            clearable
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
          <div class="text-subtitle1">Data source</div>

          <q-input
            filled
            v-model="formData.network"
            label="Network *"
            type="text"
            hint="Sensoto network identifier (within the organization)"
            :rules="[rules.REQUIRED]"
          />

          <q-input
            filled
            v-model="formData.device"
            label="Device *"
            type="text"
            hint="Sensoto device identifier (within the network)"
            :rules="[rules.REQUIRED]"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.period_in_minutes"
            label="Period (in minutes) *"
            :rules="[rules.REQUIRED, rules.INTEGER, ruleFactories.MIN(0)]"
          >
            <template #append>
              <help-button termHelp="period" />
            </template>
          </q-input>

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
  IngestExternalApiSensotoCreate,
  IngestExternalApiSensotoUpdate,
} from '../services/ingest_external_api_sensoto/types';
import type { PermissionGroup } from '@/services/permission_group/types';
import { ruleFactories, rules } from '@/utils/validation/rules';
import HelpButton from '@/components/HelpButton.vue';
import { ref } from 'vue';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<IngestExternalApiSensotoCreate | IngestExternalApiSensotoUpdate>({
  default: () => ({
    name: '',
    permission_group_id: null,
    description: null,
    network: null,
    device: null,
    organization: 'open',
    sync_enabled: false,
    sync_interval_in_minutes: null,
    token: null,
  }),
});

const isPwd = ref(true);
</script>

<style scoped></style>
