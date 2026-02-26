<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New SFTP Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new" />
      </div>
    </div>

    <q-card class="q-mb-lg" flat>
      <q-card-section>
        <q-form @submit.prevent="save" class="q-gutter-md">
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

          <q-select
            outlined
            class="q-mb-md"
            :disable="!formData.permission_group_id"
            v-model="formData.parser_csv_id"
            use-input
            emit-value
            map-options
            clearable
            :options="filteredCsvParserOptions"
            @filter="filterCsvParser"
            option-value="id"
            option-label="name"
            label="Select the parser *"
            :rules="[(val) => !!val || 'Parser is required']"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey"> No results </q-item-section>
              </q-item>
            </template>
          </q-select>

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
import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import type { IngestSftpCreate } from 'src/services/ingest_sftp/types';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
import { useCsvParserStore } from 'stores/parserCsvStore';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';

const sftpStore = useIngestSftpStore();
const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestSftpCreate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_csv_id: null,
  filename_pattern: null,
});

const isLoading = ref(false);

const filteredCsvParserOptions = ref([...csvParserStore.csvParserList]);

watch(
  () => formData.value.permission_group_id,
  async (newId) => {
    if (newId) {
      await csvParserStore.dispatchGetListbyPermissionGroup(newId);
    }
  },
);

async function save() {
  const data: IngestSftpCreate = {
    permission_group_id: formData.value.permission_group_id,
    name: formData.value.name,
    description: formData.value.description,
    parser_csv_id: formData.value.parser_csv_id,
    filename_pattern: formData.value.filename_pattern,
  };
  try {
    isLoading.value = true;
    const result = await sftpStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate to detail
    await router.push(`/ingest/sftp/${result.id}`);
  } catch (error) {
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    let errorCaption = error?.response?.data?.detail || '';

    // if it is a validation error, then error.response.data.detail is an array of objects [{type:string, loc: string[], msg: string, input: any, probably an object}]
    if (typeof errorCaption === 'object') {
      errorCaption = errorCaption[0].msg;
    }

    $q.notify({
      position: 'top',
      type: 'negative',
      progress: true,
      message: 'Failed to create ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}

function filterCsvParser(val: string, update: (callback: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredCsvParserOptions.value = [...csvParserStore.csvParserList];
    });
    return;
  }

  update(() => {
    const needle = val.toLowerCase();
    filteredCsvParserOptions.value = csvParserStore.csvParserList.filter((v) =>
      v.name.toLowerCase().includes(needle),
    );
  });
}
</script>

<style scoped></style>
