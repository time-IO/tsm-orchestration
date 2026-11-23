<template>
  <overview-table
    :rows="rows"
    :loading="loading"
    :columns="columnsSTA"
    storage-key="sta-datastream"
    :column-widths="columnWidths"
    :rows-per-page-options="[10, 25, 50, 100]"
    row-key="@iot.id"
    binary-state-sort
    selectable
    v-model:pagination="paginationSta"
    v-model:selected="selectedSta"
    @request="onRequest"
    :filter="filter"
    dense
    virtual-scroll
    no-data-label="No STA Datastreams found"
  >
    <template #toolbar>
      <slot name="filters" />
      <q-input
        v-model="filter"
        dense
        outlined
        clearable
        hide-bottom-space
        label="Search Datastream"
        style="width: 280px"
      >
        <q-tooltip>Search for ID, Name, Sensor or Description</q-tooltip>
        <template v-slot:append>
          <q-icon name="search" />
        </template>
      </q-input>
    </template>

    <template #value-tooltip="{ col, row }">
      {{ col.name === 'name' ? row.name : col.value }}
    </template>

    <template #actions="{ row }">
      <q-btn
        flat
        dense
        round
        size="sm"
        icon="open_in_new"
        :href="row['@iot.selfLink']"
        target="_blank"
      >
        <q-tooltip>Open in SensorThings API</q-tooltip>
      </q-btn>
    </template>
  </overview-table>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import OverviewTable from '@/components/common/OverviewTable.vue';
import type { ColumnWidths } from '@/utils/overview_table_utils';
import type { QuasarPaginationInterface, StaDatastream } from '@/services/sta/types';
import type { QTableRequestProp } from '@/services/types';
import { extractStreamName } from '@/utils/sta_utils';

const filter = defineModel<string>('filter', { default: '' });
const paginationSta = defineModel<QuasarPaginationInterface>('paginationSta');
const selectedSta = defineModel<StaDatastream[]>('selectedSta');

const emit = defineEmits(['onRequest']);

defineProps<{
  rows: StaDatastream[];
  loading: boolean;
}>();

const columnWidths: ColumnWidths = {
  '@iot.id': { min: 6, default: 6, max: 6 },
  name: { min: 12, default: 24 },
  thing: { min: 10, default: 24 },
  sensor: { min: 10, default: 22 },
  description: { min: 16, default: 18 },
  action: { min: 6, max: 6, default: 6 },
};

const columnsSTA: QTableColumn[] = [
  {
    name: '@iot.id',
    label: 'ID',
    field: (row: StaDatastream) => row['@iot.id'],
    align: 'left',
    sortable: true,
  },
  {
    name: 'name',
    label: 'Name',
    field: (row: StaDatastream) => extractStreamName(row.name),
    align: 'left',
    sortable: true,
  },
  {
    name: 'thing',
    label: 'Thing',
    field: (row: StaDatastream) => row.Thing?.name,
    align: 'left',
    sortable: true,
  },
  {
    name: 'sensor',
    label: 'Sensor',
    field: (row: StaDatastream) => row.Sensor?.name || '',
    align: 'left',
    sortable: true,
  },
  {
    name: 'description',
    label: 'Description',
    field: (row: StaDatastream) => row.description || '',
    align: 'left',
    sortable: false,
  },
  { name: 'action', label: '', align: 'center', field: () => '' },
];

function onRequest({ pagination }: QTableRequestProp) {
  const { page, rowsPerPage, sortBy, descending } = pagination;

  emit('onRequest', { page, rowsPerPage, sortBy, descending });
}
</script>
