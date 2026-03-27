<template>
  <q-page class="q-pa-lg">
    <h5 class="q-mb-none">Ingest - External Api</h5>
    <h6 class="q-mt-none">Umweltbundesamt (UBA) Air Data</h6>
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

    <ingest-overview-table
      class="q-mt-sm"
      ingest-path="/ingest/external-api/uba"
      :columns="default_ingest_columns"
      :rows="store.ingestExternalApiUbaList"
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
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import {
  default_ingest_columns,
  defaultPagination,
  updatePagination,
} from 'src/utils/pagination_utils';
import { useIngestExternalApiUbaStore } from 'stores/ingestExternalApiUbaStore';
import TriggerExternalApiDialog from 'components/TriggerExternalApiDialog.vue';
import { TRIGGER_EXTERNAL_API_PROVIDER } from 'src/utils/trigger_utils';
import type { IngestExternalApiUbaPublic } from 'src/services/ingest_external_api_uba/types';

const store = useIngestExternalApiUbaStore();

const pagination = ref<QTableRequestPropPagination>(defaultPagination);
const newIngestRoute = '/ingest/new/external-api/uba';

const selection = ref<IngestExternalApiUbaPublic[]>([]);
const selectedIds = computed(() => {
  return selection.value.map((item) => item.id);
});

const showTriggerDialog = ref(false);

async function loadIngest(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await store.dispatchGetList(page, rowsPerPage);
  updatePagination(pagination, data);
}

const openTriggerDialog = () => {
  showTriggerDialog.value = true;
};
</script>

<style scoped></style>
