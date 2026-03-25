<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit External SFTP Ingest</h5>
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

          <permission-group-select
            v-model="formData.permission_group_id"
            :preselectedItem="itemPermissionGroup"
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
                :disable="!permissionGroupId"
                v-model="formData.parser_csv_id"
                :permission_group_id="permissionGroupId"
                :preselectedItem="itemParser"
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
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import type { IngestExternalSftpUpdate } from 'src/services/ingest_external_sftp/types';
import { useIngestExternalSftpStore } from 'stores/ingestExternalSftpStore';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import CsvParserSelect from 'components/CsvParserSelect.vue';
import type { CsvParserPublic } from 'src/services/parser_csv/types';
import type { PermissionGroup } from 'src/services/permission_group/types';

const ingestExternalSftpStore = useIngestExternalSftpStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestExternalSftpUpdate>({
  permission_group_id: null,
  name: null,
  description: null,
  parser_csv_id: null,
  filename_pattern: null,
  uri: null,
  path: null,
  password: null,
  username: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
});

const isLoading = ref(false);
const isPwd = ref(true);

const permissionGroupId = ref<number | null>(null);
const itemParser = ref<CsvParserPublic | null>(null);
const itemPermissionGroup = ref<PermissionGroup | null>(null);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await ingestExternalSftpStore.dispatchGetOne(id);

      itemParser.value = data.csv_parser;
      permissionGroupId.value = data.permission_group_id || null;
      itemPermissionGroup.value = data.permission_group;

      formData.value = {
        permission_group_id: data.permission_group_id || null,
        name: data.name || null,
        description: data.description || null,
        parser_csv_id: data.parser_csv_id || null,
        filename_pattern: data.filename_pattern || null,
        uri: data.uri || null,
        path: data.path || null,
        password: data.password || null,
        username: data.username || null,
        sync_enabled: data.sync_enabled || false,
        sync_interval_in_minutes: data.sync_interval_in_minutes || null,
      };
    } catch {
      $q.notify({
        type: 'negative',
        message: 'Failed to load ingest data',
      });
      await router.push('/ingest');
    }
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/external-sftp/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestExternalSftpUpdate = {
      permission_group_id: formData.value.permission_group_id || null,
      name: formData.value.name || null,
      description: formData.value.description || null,
      parser_csv_id: formData.value.parser_csv_id || null,
      filename_pattern: formData.value.filename_pattern || null,
      uri: formData.value.uri || null,
      path: formData.value.path || null,
      password: formData.value.password || null,
      username: formData.value.username || null,
      sync_enabled: formData.value.sync_enabled || false,
      sync_interval_in_minutes: formData.value.sync_interval_in_minutes || null,
    };

    isLoading.value = true;

    await ingestExternalSftpStore.dispatchUpdate(id, data);

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
</script>

<style scoped></style>
