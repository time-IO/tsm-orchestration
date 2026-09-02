<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">External API Ingest</h5>
    <h6 class="q-mt-none">Neutron Monitor</h6>
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
                    <q-item-label>Station</q-item-label>
                    <q-item-label caption>{{ item.station.station_id }}</q-item-label>
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
                    <q-item-label>Time Resolution</q-item-label>
                    <q-item-label caption v-if="item.time_resolution_in_minutes">
                      {{ item.time_resolution_in_minutes }} minutes
                    </q-item-label>
                    <q-item-label caption v-else> No time resolution was set </q-item-label>
                  </q-item-section>
                </q-item>

                <q-item>
                  <q-item-section>
                    <q-item-label>Sync Enabled</q-item-label>
                    <q-item-label caption>
                      <q-badge :color="item.sync_enabled ? 'positive' : 'negative'">
                        {{ item.sync_enabled ? 'Yes' : 'No' }}
                      </q-badge>
                    </q-item-label>
                  </q-item-section>
                </q-item>

                <q-item v-if="item.sync_enabled">
                  <q-item-section>
                    <q-item-label>Sync Interval</q-item-label>
                    <q-item-label caption>
                      {{ item.sync_interval_in_minutes }} minutes
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

      <ingest-tools-section :uuid="item.uuid" :ingest-id="item.id" trigger-type="external-api" />
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
import type { IngestExternalApiNeutronMonitorPublic } from 'src/services/ingest_external_api_neutron_monitor/types';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
import CopyBtn from 'components/CopyBtn.vue';
import IngestToolsSection from 'components/IngestToolsSection.vue';

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const store = useIngestExternalApiNeutronMonitorStore();

const item = ref<IngestExternalApiNeutronMonitorPublic | null>(null);
const deleteDialog = ref(false);
const isLoading = ref(false);

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

const basePath = '/ingest/external-api/nm/';

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
</script>

<style scoped></style>
