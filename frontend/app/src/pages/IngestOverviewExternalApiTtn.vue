<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Ingest - External Api</h5>
    <h6 class="q-mt-none">The Things network</h6>
    <q-card-actions class="q-pa-none">
      <q-btn label="back" icon="chevron_left" to="/ingest/external-api" />
      <q-space> </q-space>
      <q-btn color="green" label="Add Ingest" :to="newIngestRoute" />
    </q-card-actions>

    <q-card-actions class="q-pa-none q-mt-md">
      <q-space> </q-space>
      <q-btn
        :disable="selection.length === 0"
        color="primary"
        label="Trigger"
        @click="openTriggerDialog"
      >
        <q-tooltip>Select multiple rows you want to synchronise historic data</q-tooltip>
      </q-btn>
    </q-card-actions>
    <overview-filter
      class="q-mt-md"
      v-model:name="store.filters.name"
      v-model:permission_group_id="store.filters.permission_group_id"
      v-model:date_from="store.filters.date_from"
      v-model:date_to="store.filters.date_to"
      @apply-filters="store.applyFilters"
    />
    <ingest-overview-table
      class="q-mt-sm"
      ingest-path="/ingest/external-api/ttn"
      :columns="default_ingest_columns"
      :rows="store.rows"
      @onRequest="loadIngest"
      selection="multiple"
      v-model:pagination="pagination"
      v-model:selected="selection"
    />
  </q-page>
  <trigger-external-api-dialog
    v-model="showTriggerDialog"
    :provider="TRIGGER_EXTERNAL_API_PROVIDER.TTN"
    :ids_to_trigger="selectedIds"
    @success="selection = []"
  />
</template>

<script setup lang="ts">
import IngestOverviewTable from 'components/IngestOverviewTable.vue';
import { computed, ref } from 'vue';
import type { QTableRequestProp } from 'src/services/types';
import {
  default_ingest_columns,
} from 'src/utils/pagination_utils';
import { useIngestExternalApiTheThingsNetworkStore } from 'stores/ingestExternalApiTheThingsNetworkStore';
import { TRIGGER_EXTERNAL_API_PROVIDER } from 'src/utils/trigger_utils';
import TriggerExternalApiDialog from 'components/TriggerExternalApiDialog.vue';
import type { IngestExternalApiTheThingsNetworkPublic } from 'src/services/ingest_external_api_the_things_network/types';
import OverviewFilter from 'components/OverviewFilter.vue';

const store = useIngestExternalApiTheThingsNetworkStore();

const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

const newIngestRoute = '/ingest/new/external-api/ttn';

const selection = ref<IngestExternalApiTheThingsNetworkPublic[]>([]);
const selectedIds = computed(() => {
  return selection.value.map((item) => item.id);
});

const showTriggerDialog = ref(false);

async function loadIngest(requestProp: QTableRequestProp) {
  await store.onRequest(requestProp);
}

const openTriggerDialog = () => {
  showTriggerDialog.value = true;
};
</script>

<style scoped></style>
