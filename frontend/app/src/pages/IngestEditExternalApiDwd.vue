<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit External Api Ingest</h5>
    <h6 class="q-mt-none">Deutscher Wetterdienst</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="detailRoute" />
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
import { ref, onMounted, computed} from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import type { IngestExternalApiDwdUpdate } from 'src/services/ingest_external_api_dwd/types';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import { useIngestExternalApiDwdStore } from 'stores/ingestExternalApiDwdStore';

// Composition API
const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const dwdStore = useIngestExternalApiDwdStore();
const permissionGroupStore = usePermissionGroupStore();

// Reactive data
const isLoading = ref(false);
const formData = ref<Partial<IngestExternalApiDwdUpdate>>({
  name: '',
  permission_group_id: null,
  description: '',
  station_id: null,
  sync_enabled: false,
});
const syncInterval = ref(1440);

// Load existing data when component mounts
onMounted(async () => {
  if (route.params.id) {
    try {
      await permissionGroupStore.dispatchGetList();

      const id = Number(route.params.id);
      const data = await dwdStore.dispatchGetOne(id);

      formData.value = {
        name: data.name || '',
        permission_group_id: data.permission_group_id || null,
        description: data.description || '',
        station_id: data.station_id || null,
        sync_enabled: data.sync_enabled || false,
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
    return `/ingest/external-api-dwd/${id}`;
  }
  return '';
});

// Save changes
async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);
    const data: IngestExternalApiDwdUpdate = {
      name: formData.value.name || '',
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || '',
      station_id: formData.value.station_id || null,
      sync_enabled: formData.value.sync_enabled || false,
    };

    isLoading.value = true;

    await dwdStore.dispatchUpdate(id, data);

    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Updated successfully',
    });

    // Navigate back to detail
    await router.push(detailRoute.value);
  } catch (error) {
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    const errorCaption = error?.response?.data?.detail || '';

    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to update ingest configuration',
      progress: true,
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
