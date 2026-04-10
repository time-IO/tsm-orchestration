<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">{{ title }}</h5>
    <h6 class="q-mt-none">TSystems</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="backRoute" />
      </div>
    </div>

    <div class="text-caption text-grey">
      For more information on TSystems API properties, visit the API documentation
      <a
        href="https://sensorstation.caritc.de/sensorstation-management/swagger-ui/index.html"
        target="_blank"
        >here</a
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
            :rules="[(val) => !!val || 'Name is required']"
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
            class="q-mb-md"
            v-model="formData.group"
            label="Group *"
            :rules="[(val) => !!val || 'Group is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.station_id"
            label="Station ID *"
            :rules="[(val) => !!val || 'Station ID is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.tsystems_username"
            label="Username *"
            :rules="[(val) => !!val || 'Username is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.tsystems_password"
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
                disable
                v-model.number="syncInterval"
                label="Sync Interval (minutes)"
                type="number"
                hint="Fixed interval for automatic synchronization"
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
import { ref } from 'vue';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import type {
  IngestExternalApiTSystemsCreate,
  IngestExternalApiTSystemsUpdate,
} from 'src/services/ingest_external_api_tsystems/types';
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

const formData = defineModel<IngestExternalApiTSystemsCreate | IngestExternalApiTSystemsUpdate>({
  default: {
    name: '',
    permission_group_id: null,
    description: null,
    sync_enabled: false,
    group: null,
    station_id: null,
    tsystems_username: null,
    tsystems_password: null,
  },
});

const isPwd = ref(true);
const syncInterval = ref(60);
</script>

<style scoped></style>
