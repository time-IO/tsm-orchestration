<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">External MQTT Ingest</h5>
    <div class="row">
      <div class="col">
        <q-btn class="q-mb-lg" icon="chevron_left" label="back" :to="backUrl" />
      </div>
    </div>

    <div v-if="isLoading" class="q-pa-md">
      <q-spinner color="primary" size="3em" />
    </div>

    <div v-else-if="item">
      <q-card>
        <q-card-section>
          <div class="text-h5 ellipsis" style="max-width: 100%">{{ item.name }}</div>
          <q-tooltip>
            {{ item.name }}
          </q-tooltip>
          <div class="text-subtitle1" style="max-width: 100%">{{ item.description }}</div>
        </q-card-section>

        <q-separator />

        <q-card-section>
          <div class="row q-col-gutter-md">
            <div class="col-md-6">
              <q-list>
                <q-item>
                  <q-item-section>
                    <q-item-label>ID</q-item-label>
                    <q-item-label caption>{{ item.id }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>UUID</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{ item.uuid }}</q-item-label>
                      <copy-btn title="Copy UUID" :text-to-copy="item.uuid" />
                      <visualization-link-btn :uuid="item.uuid" />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Permission Group</q-item-label>
                    <q-item-label caption>{{ item.permission_group?.name || 'N/A' }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>MQTT Address</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{ item.external_mqtt_address }}</q-item-label>
                      <copy-btn
                        title="Copy MQTT address"
                        :text-to-copy="item.external_mqtt_address"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>MQTT Port</q-item-label>
                    <q-item-label caption>{{ item.external_mqtt_port }}</q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>MQTT Topic</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{ item.external_mqtt_topic }}</q-item-label>
                      <copy-btn title="Copy MQTT topic" :text-to-copy="item.external_mqtt_topic" />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>MQTT Username</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{
                        item.external_mqtt_username || 'N/A'
                      }}</q-item-label>
                      <copy-btn
                        v-if="item.external_mqtt_username"
                        title="Copy MQTT username"
                        :text-to-copy="item.external_mqtt_username"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>MQTT Password</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption class="col-2">
                        <q-input
                          borderless
                          v-model="mqttPassword"
                          :type="isPwd ? 'password' : 'text'"
                        >
                          <template v-slot:prepend>
                            <q-icon
                              :name="isPwd ? 'visibility_off' : 'visibility'"
                              class="cursor-pointer"
                              @click="isPwd = !isPwd"
                            />
                          </template>
                        </q-input>
                      </q-item-label>
                      <copy-btn
                        v-if="item.external_mqtt_password"
                        title="Copy MQTT password"
                        :text-to-copy="item.external_mqtt_password"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>CA Certificate</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{
                        shortenText(item.external_mqtt_ca_cert) || 'Not set'
                      }}</q-item-label>
                      <copy-btn
                        v-if="item.external_mqtt_ca_cert"
                        title="Copy CA certificate"
                        :text-to-copy="item.external_mqtt_ca_cert"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Client Certificate</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{
                        shortenText(item.external_mqtt_client_cert) || 'Not set'
                      }}</q-item-label>
                      <copy-btn
                        v-if="item.external_mqtt_client_cert"
                        title="Copy client certificate"
                        :text-to-copy="item.external_mqtt_client_cert"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Client Key</q-item-label>
                    <div class="row items-center">
                      <q-item-label caption>{{
                        shortenText(item.external_mqtt_client_key) || 'Not set'
                      }}</q-item-label>
                      <copy-btn
                        v-if="item.external_mqtt_client_key"
                        title="Copy client key"
                        :text-to-copy="item.external_mqtt_client_key"
                      />
                    </div>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Created At (UTC)</q-item-label>
                    <q-item-label caption>{{ formatDate(item.created_at) }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>

            <div class="col-md-6">
              <q-list>
                <q-item>
                  <q-item-section>
                    <q-item-label>Parser</q-item-label>
                    <q-item-label caption>
                      {{ item.parser.name }}
                      <q-icon name="launch" class="cursor-pointer" @click="openParser">
                        <q-tooltip> Open in new window </q-tooltip>
                      </q-icon>
                    </q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Enabled</q-item-label>
                    <q-item-label caption>
                      <q-badge :color="item.enabled ? 'positive' : 'negative'">
                        {{ item.enabled ? 'Yes' : 'No' }}
                      </q-badge>
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions>
          <q-btn :to="editRoute" color="primary" flat> Edit </q-btn>
          <q-space />
          <q-btn :to="copyRoute" color="black" flat> Copy </q-btn>
          <q-space />
          <!--          <q-btn color="negative" flat @click="openDeleteDialog"> Delete </q-btn>-->
        </q-card-actions>
      </q-card>
    </div>

    <q-dialog v-model="deleteDialog" persistent>
      <q-card>
        <q-card-section>
          <h6 class="q-mt-none">Confirm Delete</h6>
        </q-card-section>

        <q-card-section> Are you sure you want to delete this item? </q-card-section>

        <q-card-actions align="right">
          <q-btn v-close-popup color="primary" flat label="Cancel" />
          <q-space />
          <q-btn color="negative" flat label="Delete" @click="deleteItem" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import type { IngestExternalMqttPublic } from 'src/services/ingest_external_mqtt/types';
import { useIngestExternalMqttStore } from 'stores/ingestExternalMqttStore';
import CopyBtn from 'components/CopyBtn.vue';
import VisualizationLinkBtn from 'components/VisualizationLinkBtn.vue';

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const store = useIngestExternalMqttStore();

const item = ref<IngestExternalMqttPublic | null>(null);
const deleteDialog = ref(false);
const isLoading = ref(false);
const isPwd = ref(true);

const backUrl = '/ingest';

onMounted(async () => {
  try {
    isLoading.value = true;
    const id = Number(route.params.id);

    if (!isNaN(id)) {
      item.value = await store.dispatchGetOne(id);
    }
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to load ingest data',
    });
  } finally {
    isLoading.value = false;
  }
});

const basePath = '/ingest/external-mqtt/';

const mqttPassword = computed({
  get: () => item.value?.external_mqtt_password || '',
  set: () => {},
});

const editRoute = computed(() => {
  if (item.value?.id) {
    return `${basePath}${item.value.id}/edit`;
  }
  return '';
});

const copyRoute = computed(() => {
  if (item.value?.id) {
    return `${basePath}${item.value.id}/copy`;
  }
  return '';
});

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

// const openDeleteDialog = () => {
//   deleteDialog.value = true;
// };

const deleteItem = async () => {
  if (!item.value) {
    return;
  }

  try {
    await store.dispatchDelete(item.value.id);
    $q.notify({
      type: 'positive',
      message: 'Item deleted successfully',
    });
    await router.push(backUrl);
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete item',
    });
  } finally {
    deleteDialog.value = false;
  }
};

const openParser = () => {
  if (item.value?.parser?.id && item.value?.parser?.parser_type) {
    const route = router.resolve({
      path: `/parser/${item.value.parser.parser_type}/${item.value.parser.id}`,
    });

    window.open(route.href, '_blank');
  }
};

const shortenText = (key: string | null) => {
  if (!key) return '';
  // Show first 10 chars, last 10 chars, and middle dots
  if (key.length <= 25) return key;
  return `${key.substring(0, 10)}...${key.substring(key.length - 10)}`;
};
</script>

<style scoped></style>
