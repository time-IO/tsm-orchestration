<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit External Api Ingest</h5>
    <h6 class="q-mt-none">TSystems</h6>
    <div class="row">
      <div class="col">
        <q-btn label="back" class="q-mb-lg" icon="chevron_left" :to="detailRoute" />
      </div>
    </div>

    <div class="text-caption text-grey">
      For more information on TSystems API properties, visit the API documentation
      <a
        href="https://sensorstation.caritc.de/sensorstation-management/swagger-ui/index.html"
        target="_blank"
        >here</a
      >.
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

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.group"
            label="Group *"
            :rules="[(val) => !!val || 'Group is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.station_id"
            label="Station ID *"
            :rules="[(val) => !!val || 'Station ID is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.tsystems_username"
            label="Username *"
            :rules="[(val) => !!val || 'Username is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.tsystems_password"
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
import {computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { usePermissionGroupStore } from 'stores/permissionGroupStore';
import type { IngestExternalApiTSystemsUpdate } from 'src/services/ingest_external_api_tsystems/types';
import { useIngestExternalApiTSystemsStore } from 'stores/ingestExternalApiTSystemsStore';

const tsystemsStore = useIngestExternalApiTSystemsStore();
const permissionGroupStore = usePermissionGroupStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const syncInterval = ref(60);

const formData = ref<Partial<IngestExternalApiTSystemsUpdate>>({
  name: '',
  permission_group_id: null,
  description: null,
  sync_enabled: false,
  group: null,
  station_id: null,
  tsystems_username: null,
  tsystems_password: null,
});

const isLoading = ref(false);
const isPwd = ref(true);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await tsystemsStore.dispatchGetOne(id);

      formData.value = {
        name: data.name || null,
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        sync_enabled: data.sync_enabled || false,
        group: data.group || null,
        station_id: data.station_id || null,
        tsystems_username: data.tsystems_username || null,
        tsystems_password: data.tsystems_password || null,
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

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/external-api-tsystems/${id}`;
  }
  return '';
});


async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestExternalApiTSystemsUpdate = {
      name: formData.value.name || null,
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || null,
      sync_enabled: formData.value.sync_enabled || false,
      group: formData.value.group || null,
      station_id: formData.value.station_id || null,
      tsystems_username: formData.value.tsystems_username || null,
      tsystems_password: formData.value.tsystems_password || null,
    };

    isLoading.value = true;
    await tsystemsStore.dispatchUpdate(id, data);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Saved successfully',
    });

    // Navigate back to list
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
      message: 'Failed to create ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped></style>
