<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Edit MQTT Ingest</h5>
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
            v-model="formData.uri"
            label="Broker URI *"
            :rules="[(val) => !!val || 'Broker URI is required']"
          />

          <q-input
            filled
            class="q-mb-md"
            v-model="formData.topic"
            label="Topic *"
            :rules="[(val) => !!val || 'Topic is required']"
          />

          <q-select
            outlined
            class="q-mb-md"
            v-model="formData.mqtt_parser_id"
            use-input
            emit-value
            map-options
            clearable
            :options="filteredMqttParserOptions"
            @filter="filterMqttParser"
            option-value="id"
            option-label="name"
            label="Select the parser *"
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
import type { IngestMqttUpdate } from 'src/services/ingest_mqtt/types';
import { useIngestMqttStore } from 'stores/ingestMqttStore';
import { useMqttParserStore } from 'stores/mqttParserStore';

const mqttStore = useIngestMqttStore();
const permissionGroupStore = usePermissionGroupStore();
const mqttParserStore = useMqttParserStore();
const $q = useQuasar();
const router = useRouter();
const route = useRoute();

const formData = ref<IngestMqttUpdate>({
  name: null,
  permission_group_id: null,
  description: null,
  topic: null,
  uri: null,
  mqtt_parser_id: null,
});

const isLoading = ref(false);

const filteredMqttParserOptions = ref([...mqttParserStore.mqttParsers]);

onMounted(async () => {
  if (route.params.id) {
    try {
      const id = Number(route.params.id);
      const data = await mqttStore.dispatchGetOne(id);

      formData.value = {
        name: data.name || null,
        permission_group_id: data.permission_group_id || null,
        description: data.description || null,
        topic: data.topic || null,
        uri: data.uri || null,
        mqtt_parser_id: data.mqtt_parser_id || null,
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

  try {
    await mqttParserStore.dispatchGetList();
    filteredMqttParserOptions.value = [...mqttParserStore.mqttParsers];
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch parser options',
    });
  }
});

const detailRoute = computed(() => {
  if (route.params.id) {
    const id = Number(route.params.id);
    return `/ingest/mqtt/${id}`;
  }
  return '';
});

async function save() {
  if (!route.params.id) return;

  try {
    const id = Number(route.params.id);

    const data: IngestMqttUpdate = {
      name: formData.value.name || null,
      permission_group_id: formData.value.permission_group_id || null,
      description: formData.value.description || null,
      topic: formData.value.topic || null,
      uri: formData.value.uri || null,
      mqtt_parser_id: formData.value.mqtt_parser_id || null,
    };

    isLoading.value = true;

    await mqttStore.dispatchUpdate(id, data);

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
      message: 'Failed to create ingest',
      caption: errorCaption,
    });
  } finally {
    isLoading.value = false;
  }
}

function filterMqttParser(val: string, update: (callback: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredMqttParserOptions.value = [...mqttParserStore.mqttParsers];
    });
    return;
  }

  update(() => {
    const needle = val.toLowerCase();
    filteredMqttParserOptions.value = mqttParserStore.mqttParsers.filter((v) =>
      v.name.toLowerCase().includes(needle),
    );
  });
}
</script>

<style scoped></style>
