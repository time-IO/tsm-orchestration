<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Ingest - Mqtt</h5>
    <q-card-actions class="q-pa-none">
      <q-btn label="back" icon="chevron_left" to="/ingest" />
      <q-space> </q-space>
      <q-btn color="green" label="Add Ingest" :to="newIngestRoute" />
    </q-card-actions>
    <ingest-overview-table
      class="q-mt-sm"
      ingest-path="/ingest/mqtt"
      :columns="default_ingest_columns"
      :rows="store.ingestMqttList"
      @onRequest="loadIngest"
      v-model:pagination="pagination"
    />
  </q-page>
</template>

<script setup lang="ts">
import IngestOverviewTable from 'components/IngestOverviewTable.vue';
import { ref } from 'vue';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import {
  default_ingest_columns,
  defaultPagination,
  updatePagination,
} from 'src/utils/pagination_utils';
import { useIngestMqttStore } from 'stores/ingestMqttStore';

const store = useIngestMqttStore();

const pagination = ref<QTableRequestPropPagination>(defaultPagination);
const newIngestRoute = '/ingest/new/mqtt';

async function loadIngest(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await store.dispatchGetList(page, rowsPerPage);
  updatePagination(pagination, data);
}
</script>

<style scoped></style>
