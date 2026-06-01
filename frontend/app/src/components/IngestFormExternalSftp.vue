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

          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">SFTP Settings</div>

            <div class="q-mt-md">
              <q-input
                filled
                class="q-mb-md"
                v-model="formData.filename_pattern"
                label="Filename pattern *"
                :rules="[(val) => !!val || 'Filename pattern is required']"
              />

              <csv-parser-select
                class="q-mb-md"
                :disable="!formData.permission_group_id"
                v-model="formData.parser_id"
                :permission_group_id="formData.permission_group_id!"
                :preselected_item_id="itemParserId"
              />
            </div>
          </q-card-section>

          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">External Server Settings</div>

            <div class="q-mt-md">
              <q-input
                filled
                class="q-mb-md"
                v-model="formData.uri"
                label="Fileserver URI *"
                :rules="[(val) => !!val || 'Fileserver URI is required']"
              />

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.path"
                label="Path *"
                :rules="[(val) => !!val || 'Path is required']"
              />

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.username"
                label="Username *"
                :rules="[(val) => !!val || 'Username is required']"
              />

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.password"
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
            </div>
          </q-card-section>

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
                :disable="!formData.sync_enabled"
                v-model.number="formData.sync_interval_in_minutes"
                :label="
                  formData.sync_enabled
                    ? 'Sync Interval (in minutes) *'
                    : 'Sync Interval (in minutes)'
                "
                type="number"
                :rules="[
                  (val) =>
                    !formData.sync_enabled ||
                    (val !== null && val !== '' && val > 0) ||
                    'Interval must be a positive number when sync is enabled',
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
import CsvParserSelect from 'components/CsvParserSelect.vue';
import { ref } from 'vue';
import type {
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate,
} from 'src/services/ingest_external_sftp/types';
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

const formData = defineModel<IngestExternalSftpCreate | IngestExternalSftpUpdate>({
  default: {
    permission_group_id: null,
    name: null,
    description: null,
    parser_id: null,
    filename_pattern: null,
    uri: null,
    path: null,
    password: null,
    username: null,
    sync_enabled: false,
    sync_interval_in_minutes: null,
  },
});

const isPwd = ref(true);
</script>

<style scoped></style>
