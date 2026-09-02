<template>
  <div class="row">
    <div class="text-h6">Created Datastreams</div>
  </div>
  <div class="row">
    <div class="col">
      <q-btn
        dense
        flat
        icon="add"
        label="Create Datastream"
        color="secondary"
        @click="showCreateDialog = true"
      />
    </div>
  </div>
  <q-table
    :rows="filteredCreatedRows"
    :columns="columnsCreated"
    row-key="name"
    selection="multiple"
    v-model:selected="selectedCreated"
    v-model:pagination="paginationCreated"
    :rows-per-page-options="rowsPerPageOptionsCreated"
    flat
    bordered
    dense
    virtual-scroll
  >
    <template #body-cell-name="slotProps">
      <q-td :props="slotProps">
        <span>{{ truncateText(slotProps.value, 40) }}</span>
        <q-tooltip>{{ slotProps.value }}</q-tooltip>
      </q-td>
    </template>

    <template #body-cell-thing="slotProps">
      <q-td :props="slotProps">
        <span>{{ truncateText(slotProps.value, 100) }}</span>
        <q-tooltip>{{ slotProps.value }}</q-tooltip>
      </q-td>
    </template>

    <template #body-cell-actions="slotProps">
      <q-td :props="slotProps">
        <q-btn flat dense round size="sm" icon="open_in_new" color="grey" disable />
      </q-td>
    </template>
  </q-table>
  <q-dialog v-model="showCreateDialog">
    <q-card style="min-width: 50vh" class="q-pa-md">
      <q-card-section class="row q-mb-sm" horizontal>
        <div class="text-h6">Create Datastream</div>
        <q-space />
        <q-btn v-close-popup dense flat icon="close" round />
      </q-card-section>
      <sta-temporary-datastream-creation
        :already-selected-thing="alreadySelectedThing"
        :existing-datastreams="existingDatastreams"
        @add-temporary="onAddTemporary"
        :permission_group_id="permission_group_id"
      />
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import StaTemporaryDatastreamCreation from 'components/StaTemporaryDatastreamCreation.vue';
import type {
  Datastream,
  QuasarPaginationInterface,
  StaEntity,
  TemporaryDatastream,
} from 'src/services/sta/types';
import { truncateText } from 'src/utils/string_utils';
import type { QTableColumn } from 'quasar';

const selectedCreated = defineModel<TemporaryDatastream[]>('selectedCreated');
const paginationCreated = defineModel<QuasarPaginationInterface>('paginationCreated');

const { alreadySelectedThing, existingDatastreams } = defineProps<{
  alreadySelectedThing: StaEntity | null;
  existingDatastreams: Datastream[];
  filteredCreatedRows: TemporaryDatastream[];
  permission_group_id: number;
}>();

const emit = defineEmits<{
  (e: 'add-temporary', ds: TemporaryDatastream): void;
}>();

const showCreateDialog = ref(false);

const rowsPerPageOptionsCreated = ref<Array<number>>([10, 25, 50, 100, 0]);

const columnsCreated: QTableColumn[] = [
  {
    name: 'id',
    label: 'ID',
    field: () => '-',
    align: 'left',
    style: 'width: 10%',
  },
  {
    name: 'thing',
    label: 'Thing',
    field: (r: TemporaryDatastream) => r.Thing?.name,
    align: 'left',
    style: 'width: 20%',
    sortable: true,
  },
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left',
    style: 'width: 60%',
    sortable: true,
  },
  { name: 'actions', label: '', align: 'center', style: 'width: 10%', field: () => '' },
];

function onAddTemporary(ds: TemporaryDatastream) {
  emit('add-temporary', ds);
  showCreateDialog.value = false;
}
</script>

<style scoped></style>
