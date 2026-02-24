<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
    <h6 class="q-mt-none">Deutscher Wetterdienst</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" to="/ingest/new" />
      </div>
    </div>
    <div class="text-caption text-grey">
      For more information on Deutscher Wetterdienst API properties, visit the API documentation
      <a href="https://brightsky.dev/docs/#/operations/getWeather" target="_blank">here</a>.
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

          <q-select
            filled
            v-model="formData.permission_group_id"
            :options="permissionGroupStore.permissionGroups"
            label="Permission Group *"
            option-value="id"
            option-label="name"
            emit-value
            map-options
            hint="Select the permission group this ingest belongs to"
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

          <!-- Station ID -->
          <q-input
            filled
            v-model="formData.station_id"
            label="Station ID *"
            hint="DWD station ID, typically five alphanumeric characters."
            :rules="[(val) => !!val || 'Valid station ID is required']"
          />

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
import { onMounted, ref } from 'vue';
import type { IngestExternalApiDwdCreate } from 'src/services/ingest_external_api_dwd/types';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import { useIngestExternalApiDwdStore } from 'stores/ingestExternalApiDwdStore';

const dwdStore = useIngestExternalApiDwdStore();
const permissionGroupStore = usePermissionGroupStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalApiDwdCreate>({
  name: '',
  permission_group_id: null,
  description: '',
  station_id: null,
  sync_enabled: false,
});
const syncInterval = ref(1440);
const isLoading = ref(false);

onMounted(async () => {
  try {
    await permissionGroupStore.dispatchGetList();
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch permission groups',
    });
  }
});

async function save() {
  const data: IngestExternalApiDwdCreate = {
    name: formData.value.name,
    description: formData.value.description,
    permission_group_id: formData.value.permission_group_id,
    station_id: formData.value.station_id,
    sync_enabled: formData.value.sync_enabled,
  };
  try {
    isLoading.value = true;
    const result = await dwdStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate back to list
    await router.push(`/ingest/external-api-dwd/${result.id}`);
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
</script>

<style scoped></style>
