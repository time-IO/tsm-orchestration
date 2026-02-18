<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit External Api Ingest</h5>
    <h6 class="q-mt-none">Bosch IoT</h6>
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

          <q-select
            filled
            v-model="formData.permission_group_id"
            :options="permissionGroupStore.permissionGroups"
            label="Permission Group *"
            option-value="id"
            option-label="name"
            emit-value
            map-options
            hint="Select the project this ingest belongs to"
            :rules="[(val) => !!val || 'Project is required']"
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
            v-model="formData.endpoint"
            label="Endpoint *"
            :rules="[(val) => !!val || 'Endpoint is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.sensor_id"
            label="Sensor-ID *"
            :rules="[(val) => !!val || 'Sensor-ID is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.bosch_username"
            label="Username *"
            :rules="[(val) => !!val || 'Username is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.bosch_password"
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

          <q-input
            filled
            class="q-mb-md"
            v-model.number="formData.period_in_minutes"
            label="Period (in minutes) *"
            :rules="[
              (val) => !!val || 'Period is required',
              (val) =>
                (val !== null && val !== '' && val > 0) ||
                'Interval must be a positive number when sync is enabled',
            ]"
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
import { onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import { useIngestExternalApiBoschStore } from 'stores/ingestExternalApiBoschStore';
import type { IngestExternalApiBoschUpdate } from 'src/services/ingest_external_api_bosch/types';

const boschStore = useIngestExternalApiBoschStore();
const permissionGroupStore = usePermissionGroupStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<Partial<IngestExternalApiBoschUpdate>>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  sync_interval_in_minutes: null,
  endpoint: null,
  sensor_id: null,
  bosch_username: null,
  bosch_password: null,
  period_in_minutes: null,
});

const isLoading = ref(false);
const isPwd = ref(true);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await boschStore.dispatchGetOne(id);

      formData.value = {
        name: data.name || '',
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        sync_enabled: data.sync_enabled || false,
        sync_interval_in_minutes: data.sync_interval_in_minutes || null,
        endpoint: data.endpoint || null,
        sensor_id: data.sensor_id || null,
        bosch_username: data.bosch_username || null,
        bosch_password: data.bosch_password || null,
        period_in_minutes: data.period_in_minutes || null,
      };
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
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestExternalApiBoschUpdate = {
      name: formData.value.name || '',
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || null,
      sync_enabled: formData.value.sync_enabled || false,
      sync_interval_in_minutes: formData.value.sync_interval_in_minutes || null,
      endpoint: formData.value.endpoint || null,
      sensor_id: formData.value.sensor_id || null,
      bosch_username: formData.value.bosch_username || null,
      bosch_password: formData.value.bosch_password || null,
      period_in_minutes: formData.value.period_in_minutes || null,
    };

    isLoading.value = true;
    await boschStore.dispatchUpdate(id, data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate back to list
    await router.push(`/ingest/external-api-bosch/${id}`);
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
