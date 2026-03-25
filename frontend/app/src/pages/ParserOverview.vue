<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Parsers</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" label="Add Parser" to="/parser/new" />
    </div>
    <div class="text-h5 q-mt-lg q-mb-sm">Parser - CSV</div>
    <q-table
      ref="tableRef"
      :rows="csvParserStore.csvParserList"
      :columns="columns"
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
          </div>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import { useCsvParserStore } from 'stores/parserCsvStore';
import { onMounted, ref } from 'vue';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import { updatePagination } from 'src/utils/pagination_utils';

const csvParserStore = useCsvParserStore();

const pagination = ref<QTableRequestPropPagination>({
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 25,
  rowsNumber: 10,
});

const tableRef = ref();

onMounted(() => {
  // get initial data from server (1st page)
  tableRef.value.requestServerInteraction();
});

const columns: QTableColumn[] = [
  {
    name: 'id',
    required: true,
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'permission-group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    sortable: true,
    align: 'center',
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];

async function onRequest(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await csvParserStore.dispatchGetList(page, rowsPerPage);
  updatePagination(pagination, data);
}
</script>

<style scoped></style>
