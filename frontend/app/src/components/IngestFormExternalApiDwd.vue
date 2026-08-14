<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <h6 class="q-mt-none">Deutscher Wetterdienst</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>
    <div class="text-caption text-grey">
      For more information on Deutscher Wetterdienst API properties, visit the API documentation
      <a href="https://brightsky.dev/docs/#/operations/getWeather" target="_blank">here</a>.
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
            hint="Provide additional details about this Ingest Configuration"
          />

          <!-- Station ID -->
          <q-input
            filled
            v-model="formData.station_id"
            label="Station ID *"
            hint="DWD station ID, typically five alphanumeric characters."
            :rules="[rules.REQUIRED]"
          >
            <template #append>
              <q-btn round flat icon="help_outline" @click="openDwdDocs" class="text-grey">
                <q-tooltip>View DWD station list (use Stations_id)</q-tooltip>
              </q-btn>
            </template>
          </q-input>

          <!-- Period in minutes -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.period_in_minutes"
            label="Period (in minutes)"
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
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import type {
  IngestExternalApiDwdCreate,
  IngestExternalApiDwdUpdate,
} from 'src/services/ingest_external_api_dwd/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import HelpButton from 'components/HelpButton.vue';
import { ruleFactories, rules } from 'src/utils/validation/rules';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<IngestExternalApiDwdCreate | IngestExternalApiDwdUpdate>({
  default: {
    name: '',
    permission_group_id: null,
    description: '',
    station_id: null,
    sync_enabled: false,
    sync_interval_in_minutes: null,
    period_in_minutes: null,
  },
});

function openDwdDocs() {
  window.open(
    'https://opendata.dwd.de/climate_environment/CDC/help/RR_Stundenwerte_Beschreibung_Stationen.txt',
    '_blank',
  );
}
</script>

<style scoped></style>
