<template>
  <q-table
    title="STA Datastreams"
    :rows="rows"
    :columns="columnsSTA"
    v-model:pagination="paginationSta"
    v-model:selected="selectedSta"
    :rows-per-page-options="rowsPerPageOptionsSta"
    :loading="loading"
    row-key="@iot.id"
    selection="multiple"
    :filter="filter"
    @request="onRequest"
    flat
    bordered
    dense
    virtual-scroll
    no-data-label="No STA Datastreams found"
  >
    <template v-slot:top-right>
      <q-input
        v-model="filter"
        dense
        outlined
        clearable
        label="Search Datastream"
        hint="Search for ID, Name, Sensor or Description"
        hide-hint
      >
        <template v-slot:append>
          <q-icon name="search" />
        </template>
      </q-input>
    </template>
    <template #body-cell-name="slotProps">
      <q-td :props="slotProps">
        <span>{{ truncateText(slotProps.value, 40) }}</span>
        <q-tooltip>{{ slotProps.value }}</q-tooltip>
      </q-td>
    </template>

    <template #body-cell-thing="slotProps">
      <q-td :props="slotProps">
        <span>{{ truncateText(slotProps.value, 80) }}</span>
        <q-tooltip>{{ slotProps.value }}</q-tooltip>
      </q-td>
    </template>

    <template #body-cell-sensor="slotProps">
      <q-td :props="slotProps">
        <span>{{ truncateText(slotProps.value, 60) }}</span>
        <q-tooltip>{{ slotProps.value }}</q-tooltip>
      </q-td>
    </template>

    <template #body-cell-description="slotProps">
      <q-td :props="slotProps">
        <span>{{ truncateText(slotProps.value, 20) }}</span>
        <q-tooltip>{{ slotProps.value }}</q-tooltip>
      </q-td>
    </template>

    <template #body-cell-actions="slotProps">
      <q-td :props="slotProps">
        <q-btn
          flat
          dense
          round
          size="sm"
          icon="open_in_new"
          :href="slotProps.row['@iot.selfLink']"
          target="_blank"
        />
      </q-td>
    </template>
  </q-table>
</template>

<script setup lang="ts">
import { truncateText } from 'src/utils/string_utils';
import { ref } from 'vue';
import type { QuasarPaginationInterface, StaDatastream } from 'src/services/sta/types';
import type { QTableColumn } from 'quasar';
import type { QuasarTableOnRequestInterface } from 'src/services/sta/types';

const filter = defineModel<string>('filter', { default: '' });
const paginationSta = defineModel<QuasarPaginationInterface>('paginationSta');
const selectedSta = defineModel<StaDatastream[]>('selectedSta');

const emit = defineEmits(['onRequest']);

defineProps<{
  rows: StaDatastream[];
  loading: boolean;
}>();

const rowsPerPageOptionsSta = ref<Array<number>>([10, 25, 50, 100]);

const columnsSTA: QTableColumn[] = [
  {
    name: '@iot.id',
    label: 'ID',
    field: (row: StaDatastream) => row['@iot.id'],
    align: 'left',
    sortable: false,
    style: 'width: 10%',
  },
  {
    name: 'name',
    label: 'Name',
    field: (row: StaDatastream) => row.name,
    align: 'left',
    sortable: false,
    style: 'width: 20%',
  },
  {
    name: 'thing',
    label: 'Thing',
    field: (row: StaDatastream) => row.Thing?.name,
    align: 'left',
    sortable: false,
    style: 'width: 20%',
  },
  {
    name: 'sensor',
    label: 'Sensor',
    field: (row: StaDatastream) => row.Sensor?.name || '',
    align: 'left',
    sortable: false,
    style: 'width: 20%',
  },
  {
    name: 'description',
    label: 'Description',
    field: (row: StaDatastream) => row.description || '',
    align: 'left',
    sortable: false,
    style: 'width: 20%',
  },
  { name: 'actions', label: '', align: 'center', style: 'width: 10%', field: () => '' },
];

function onRequest(params: { pagination: QuasarTableOnRequestInterface }) {
  const { page, rowsPerPage, sortBy, descending } = params.pagination;

  emit('onRequest', { page, rowsPerPage, sortBy, descending });
}
</script>

<style scoped></style>
