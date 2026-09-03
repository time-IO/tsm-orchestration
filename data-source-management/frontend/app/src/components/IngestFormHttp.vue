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

          <!-- Parser Settings -->
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

          <!-- HTTP Settings -->
          <q-card-section class="q-pa-none">
            <div class="text-h6 q-mb-md">HTTP Ingest Settings</div>

            <div class="q-mt-md">
              <q-input
                filled
                class="q-mb-md"
                v-model="formData.path_for_posts"
                label="Path for Posts *"
                :rules="[(val) => !!val || 'Path for Posts is required']"
              >
                <template #append>
                  <help-button
                    titleHelp="Path for Posts"
                    textHelp="The HTTP path endpoint where data will be posted. For example, /api/v1/data or /ingest."
                  />
                </template>
              </q-input>

              <q-select
                filled
                class="q-mb-md"
                v-model="formData.file_type"
                label="File Type *"
                :options="fileTypeOptions"
                :rules="[(val) => !!val || 'File Type is required']"
              >
                <template #append>
                  <help-button
                    titleHelp="File Type"
                    textHelp="The expected file type or data format for incoming HTTP requests (e.g., JSON, XML, CSV)."
                  />
                </template>
              </q-select>

              <q-input
                filled
                class="q-mb-md"
                v-model="formData.api_key"
                label="API Key"
                :type="isApiKeyPwd ? 'password' : 'text'"
              >
                <template v-slot:append>
                  <q-icon
                    :name="isApiKeyPwd ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer"
                    @click="isApiKeyPwd = !isApiKeyPwd"
                  />
                </template>
                <template #append>
                  <help-button
                    titleHelp="API Key"
                    textHelp="An optional API key for authenticating incoming HTTP requests."
                  />
                </template>
              </q-input>
            </div>
          </q-card-section>

          <!-- Enable Toggle -->
          <q-card-section class="q-pa-none">
            <q-toggle
              v-model="formData.enabled"
              label="Enable HTTP Ingest"
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
  IngestHttpCreate,
  IngestHttpUpdate,
} from 'src/services/ingest_http/types';
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

const formData = defineModel<IngestHttpCreate | IngestHttpUpdate>({
  default: {
    permission_group_id: null,
    name: null,
    description: null,
    parser_id: null,
    path_for_posts: null,
    file_type: null,
    api_key: null,
    enabled: false,
  },
});

const isApiKeyPwd = ref(true);

const fileTypeOptions = [
  'json',
  'xml',
  'csv',
  'text',
  'binary',
];
</script>

<style scoped></style>
