<template>
  <q-page class="q-pa-lg">
    <h5>Trigger External APIs</h5>
    <p>Select multiple rows you want to synchronise historic data</p>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn
        :disable="selection.length === 0"
        color="primary"
        label="Trigger"
        @click="openTriggerDialog"
      >
        <q-tooltip>Select multiple rows you want to synchronise historic data</q-tooltip>
      </q-btn>
    </div>
    <ingest-overview-external-api-filter
      class="q-mt-md q-mb-md"
      v-model:name="store.filters.name"
      v-model:uuid="store.filters.uuid"
      v-model:api_type="store.filters.api_type"
      v-model:permission_group_id="store.filters.permission_group_id"
      v-model:date_from="store.filters.date_from"
      v-model:date_to="store.filters.date_to"
      @apply-filters="store.applyFilters"
    />
    <ingest-overview-external-api-table
      v-model:selected="selection"
      :loading="store.loading"
      :rows="store.rows"
      :pagination="pagination"
      :columns="columns"
      selection="multiple"
      @onRequest="store.onRequest"
    />
    <trigger-external-api-dialog
      v-model="showTriggerDialog"
      :ids_to_trigger="selectedIds"
      @success="selection = []"
    />
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import IngestOverviewExternalApiTable from 'components/IngestOverviewExternalApiTable.vue';
import { useIngestExternalApiStore } from 'stores/ingestExternalApiStore';
import type { IngestExternalApiRead } from 'src/services/ingest_external_api/types';
import TriggerExternalApiDialog from 'components/TriggerExternalApiDialog.vue';
import IngestOverviewExternalApiFilter from 'components/IngestOverviewExternalApiFilter.vue';
import { default_ingest_external_api_columns } from 'src/utils/pagination_utils';

const store = useIngestExternalApiStore();

const selection = ref<IngestExternalApiRead[]>([]);
const selectedIds = computed(() => {
  return selection.value.map((item) => item.id);
});

const showTriggerDialog = ref(false);

const openTriggerDialog = () => {
  showTriggerDialog.value = true;
};

const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

const columns = computed(() =>
  default_ingest_external_api_columns
    .filter((col) => col.name !== 'action')
    .map((col) => ({
      ...col,
      align: 'left' as const,
    })),
);
</script>

<style scoped></style>
