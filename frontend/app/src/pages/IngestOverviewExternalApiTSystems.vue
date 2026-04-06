<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Ingest - External Api</h5>
    <h6 class="q-mt-none">TSystems</h6>
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
      ingest-path="/ingest/external-api/tsystems"
      :columns="default_ingest_columns"
      :rows="store.rows"
      @onRequest="loadIngest"
      selection="multiple"
      v-model:pagination="pagination"
      v-model:selected="selection"
    />
    <trigger-external-api-dialog
      v-model="showTriggerDialog"
      :provider="TRIGGER_EXTERNAL_API_PROVIDER.UBA"
      :ids_to_trigger="selectedIds"
      @success="selection = []"
    />
  </q-page>
</template>

<script setup lang="ts">
import IngestOverviewTable from 'components/IngestOverviewTable.vue';
import { computed, ref } from 'vue';
import type { QTableRequestProp } from 'src/services/types';
import {
  default_ingest_columns,
} from 'src/utils/pagination_utils';
import { useIngestExternalApiTSystemsStore } from 'stores/ingestExternalApiTSystemsStore';
import { TRIGGER_EXTERNAL_API_PROVIDER } from 'src/utils/trigger_utils';
import TriggerExternalApiDialog from 'components/TriggerExternalApiDialog.vue';
import type { IngestExternalApiTSystemsPublic } from 'src/services/ingest_external_api_tsystems/types';
import OverviewFilter from 'components/OverviewFilter.vue';

const store = useIngestExternalApiTSystemsStore();

const newIngestRoute = '/ingest/new/external-api/tsystems';

const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

const selection = ref<IngestExternalApiTSystemsPublic[]>([]);
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
