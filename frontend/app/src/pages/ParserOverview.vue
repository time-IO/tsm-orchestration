<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Parsers</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" label="Add Parser" to="/parser/new" />
    </div>
    <div class="text-h5 q-mt-lg q-mb-sm">Parser - CSV</div>

    <overview-filter
      class="q-mt-md q-mb-md"
      v-model:name="store.filters.name"
      v-model:permission_group_id="store.filters.permission_group_id"
      v-model:date_from="store.filters.date_from"
      v-model:date_to="store.filters.date_to"
      @apply-filters="store.applyFilters"
    />

    <q-table
      ref="tableRef"
      :rows="store.rows"
      :columns="default_ingest_columns"
      row-key="name"
      v-model:pagination="pagination"
      @request="onRequest"
    >
      <template v-slot:body-cell-action="props">
        <q-td :props="props">
          <div>
            <q-btn
              :to="`parser/csv/${props.row.id}`"
              flat
              outline
              color="primary"
              icon="visibility"
            >
              <q-tooltip>View details</q-tooltip>
            </q-btn>
            <q-btn
              :to="`parser/csv/${props.row.id}/edit`"
              flat
              outline
              color="secondary"
              icon="edit"
            >
              <q-tooltip>Edit parser</q-tooltip>
            </q-btn>
            <q-btn
              :to="`parser/csv/${props.row.id}/copy`"
              flat
              outline
              color="black"
              icon="content_copy"
            >
              <q-tooltip>Edit parser</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useCsvParserStore } from 'stores/parserCsvStore';
import { default_ingest_columns } from 'src/utils/pagination_utils';
import type { QTableRequestProp } from 'src/services/types';
import OverviewFilter from 'components/OverviewFilter.vue';

const store = useCsvParserStore();

const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

const tableRef = ref();

onMounted(() => {
  // get initial data from server (1st page)
  tableRef.value.requestServerInteraction();
});

async function onRequest(requestProp: QTableRequestProp) {
  await store.onRequest(requestProp);
}
</script>

<style scoped></style>
