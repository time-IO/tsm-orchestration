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
            :preselectedItem="itemPermissionGroup"
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
import type { IngestSftpCreate, IngestSftpUpdate } from 'src/services/ingest_sftp/types';
import type { PermissionGroup } from 'src/services/permission_group/types';
import HelpButton from 'components/HelpButton.vue';
import { ruleFactories, rules } from 'src/utils/validation/rules';
import ParserSelectByType from 'components/ParserSelectByType.vue';
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

const formData = defineModel<IngestSftpCreate | IngestSftpUpdate>({
  default: {
    permission_group_id: null,
    name: null,
    description: null,
    parser_id: null,
    filename_pattern: null,
  },
});
</script>

<style scoped></style>
