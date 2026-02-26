<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">New External Api Ingest</h5>
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
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useIngestExternalApiBoschStore } from 'stores/ingestExternalApiBoschStore';
import type { IngestExternalApiBoschCreate } from 'src/services/ingest_external_api_bosch/types';
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';

const boschStore = useIngestExternalApiBoschStore();
const $q = useQuasar();
const router = useRouter();

const formData = ref<IngestExternalApiBoschCreate>({
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


async function save() {
  const data: IngestExternalApiBoschCreate = {
    name: formData.value.name,
    permission_group_id: formData.value.permission_group_id,
    description: formData.value.description,
    sync_enabled: formData.value.sync_enabled,
    sync_interval_in_minutes: formData.value.sync_interval_in_minutes,
    endpoint: formData.value.endpoint,
    sensor_id: formData.value.sensor_id,
    bosch_username: formData.value.bosch_username,
    bosch_password: formData.value.bosch_password,
    period_in_minutes: formData.value.period_in_minutes,
  };
  try {
    isLoading.value = true;
    const result = await boschStore.dispatchCreate(data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate back to list
    await router.push(`/ingest/external-api-bosch/${result.id}`);
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
