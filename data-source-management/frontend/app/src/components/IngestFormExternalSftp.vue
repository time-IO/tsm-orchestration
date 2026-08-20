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

          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">SFTP Settings</div>

            <div class="q-mt-md">
              <q-input
                filled
                class="q-mb-md"
                v-model="formData.filename_pattern"
                label="Filename pattern *"
                :rules="[rules.REQUIRED]"
              >
                <template #append>
                  <help-button
                    titleHelp="Filename pattern"
                    textHelp="SFTP ingest filename patterns can be defined using glob patterns
                    to specify which files to process. For example, a pattern like
                    *.csv will match all CSV files in the specified directory."
                  />
                </template>
              </q-input>

              <parser-select-by-type
                v-model="formData.parser_id"
                :permission-group-id="formData.permission_group_id"
                :disable="!formData.permission_group_id"
                :preselected-parser="itemParser"
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
                :rules="[rules.REQUIRED]"
              >
                <template #append>
                  <help-button
                    titleHelp="Fileserver URI"
                    textHelp="The external SFTP ingest file server URI uses the format
                    sftp://hostname[:port], where hostname is the server address and port is
                    optional (default: 22)."
                  />
                </template>
              </q-input>

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.path"
                label="Path *"
                :rules="[rules.REQUIRED]"
              >
                <template #append>
                  <help-button
                    titleHelp="Path"
                    textHelp="The path refers to the specific directory on the SFTP server where the files are
              located."
                  />
                </template>
              </q-input>

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.username"
                label="Username *"
                :rules="[rules.REQUIRED]"
              />

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.password"
                label="Password *"
                :type="isPwd ? 'password' : 'text'"
                :rules="[rules.REQUIRED]"
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
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate,
} from 'src/services/ingest_external_sftp/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import HelpButton from 'components/HelpButton.vue';
import { ref } from 'vue';
import ParserSelectByType from 'components/ParserSelectByType.vue';

import { ruleFactories, rules } from 'src/utils/validation/rules';
import type { ParserRead } from 'src/services/types';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  itemPermissionGroup?: PermissionGroup | null;
  itemParser?: ParserRead | null;
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
