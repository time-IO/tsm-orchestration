<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit SFTP Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="detailRoute" />
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
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import type { IngestSftpUpdate } from 'src/services/ingest_sftp/types';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
import { useCsvParserStore } from 'stores/parserCsvStore';

const sftpStore = useIngestSftpStore();
const permissionGroupStore = usePermissionGroupStore();
const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestSftpUpdate>({
  name: null,
  description: null,
  parser_csv_id: null,
  filename_pattern: null,
});

const isLoading = ref(false);

const filteredCsvParserOptions = ref([...csvParserStore.csvParserList]);
let permissionGroupId: number | null = null;

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await sftpStore.dispatchGetOne(id);

      formData.value = {
        name: data.name || null,
        description: data.description || null,
        filename_pattern: data.filename_pattern || null,
        parser_csv_id: data.parser_csv_id || null,
      };

      permissionGroupId = data.permission_group_id || null;
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load ingest data',
      });
      await router.push('/ingest');
    }
  }

  try {
    await permissionGroupStore.dispatchGetList();
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch permission groups',
    });
  }

  if (permissionGroupId !== null) {
    try {
      await csvParserStore.dispatchGetListbyPermissionGroup(permissionGroupId);
      filteredCsvParserOptions.value = [...csvParserStore.csvParserList];
    } catch {
      $q.notify({
        position: 'top',
        type: 'negative',
        message: 'Failed to fetch parser options',
      });
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/sftp/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestSftpUpdate = {
      name: formData.value.name || null,
      description: formData.value.description || null,
      parser_csv_id: formData.value.parser_csv_id || null,
      filename_pattern: formData.value.filename_pattern || null,
    };

    isLoading.value = true;
    await sftpStore.dispatchUpdate(id, data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate to detail
    await router.push(detailRoute.value);
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
      message: 'Failed to update ingest',
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
