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
            :rules="[(val) => !!val || 'Name is required']"
          />

          <permission-group-select
            v-model="formData.permission_group_id"
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
            v-model="formData.filename_pattern"
            label="Filename pattern *"
            :rules="[(val) => !!val || 'Filename pattern is required']"
          />

          <csv-parser-select
            class="q-mb-md"
            :disable="!formData.permission_group_id"
            v-model="formData.parser_csv_id"
            :permission_group_id="formData.permission_group_id"
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
import CsvParserSelect from 'components/CsvParserSelect.vue';
import type { IngestSftpCreate } from 'src/services/ingest_sftp/types';
import type { CsvParserPublic } from 'src/services/parser_csv/types';

defineProps<{
  title: string;
  isLoading: boolean;
  backRoute: string;
  permissionGroupId?: number | null;
  itemParser?: CsvParserPublic | number;
}>();

defineEmits<{
  save: [];
}>();

const formData = defineModel<IngestSftpCreate>({
  default: {
    permission_group_id: null,
    name: null,
    description: null,
    parser_csv_id: null,
    filename_pattern: null,
  },
});
</script>

<style scoped></style>
