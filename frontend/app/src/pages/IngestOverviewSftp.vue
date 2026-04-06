<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Ingest - Sftp</h5>
    <q-card-actions class="q-pa-none">
      <q-btn label="back" icon="chevron_left" to="/ingest" />
      <q-space> </q-space>
      <q-btn color="green" label="Add Ingest" :to="newIngestRoute" />
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
      ingest-path="/ingest/sftp"
      :columns="default_ingest_columns"
      :rows="store.rows"
      @onRequest="loadIngest"
      v-model:pagination="pagination"
    />
  </q-page>
</template>

<script setup lang="ts">
import IngestOverviewTable from 'components/IngestOverviewTable.vue';
import { computed } from 'vue';
import type { QTableRequestProp } from 'src/services/types';
import {
  default_ingest_columns,
} from 'src/utils/pagination_utils';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
import OverviewFilter from 'components/OverviewFilter.vue';

const store = useIngestSftpStore();

const newIngestRoute = '/ingest/new/sftp';

const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

async function loadIngest(requestProp: QTableRequestProp) {
  await store.onRequest(requestProp);
}
</script>

<style scoped></style>
