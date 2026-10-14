<template>
  <overview-table
    :rows="rows"
    :loading="loading"
    :columns="columns"
    storage-key="qcsetting"
    :col-min-widths="colMinWidths"
    :default-col-widths="defaultColWidths"
    selectable
    v-model:pagination="pagination"
    v-model:selected="selected"
    @request="onRequest"
    @delete="onDelete"
  >
    <template #actions="{ row, openDeleteDialog }">
      <q-btn :to="`${basePath}/${row.id}`" flat outline color="primary" icon="visibility">
        <q-tooltip>View details</q-tooltip>
      </q-btn>
      <q-btn :to="`${basePath}/${row.id}/edit`" flat outline color="secondary" icon="edit">
        <q-tooltip>Edit</q-tooltip>
      </q-btn>
      <q-btn :to="`${basePath}/${row.id}/copy`" flat outline color="black" icon="content_copy">
        <q-tooltip>Copy</q-tooltip>
      </q-btn>
      <q-btn flat outline color="negative" icon="delete" @click="openDeleteDialog(row.id)">
        <q-tooltip>Delete</q-tooltip>
      </q-btn>
    </template>
  </overview-table>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import type { QTableRequestProp, QTableRequestPropPagination } from '@/services/types';
import type { QualityControlSettingPublic } from '@/services/quality_control_setting/types';
import OverviewTable from '@/components/common/OverviewTable.vue';

defineProps<{
  rows: QualityControlSettingPublic[];
  loading: boolean;
}>();

const pagination = defineModel<QTableRequestPropPagination>('pagination');
const selected = defineModel<QualityControlSettingPublic[]>('selected');

const emit = defineEmits<{
  onRequest: [props: QTableRequestProp];
  // the parent closes the confirm dialog via `closeDialog` once the deletion succeeded
  delete: [id: number | null, closeDialog: () => void];
}>();

function onRequest(props: QTableRequestProp) {
  emit('onRequest', props);
}

const onDelete = (id: number | null, closeDialog: () => void) => {
  emit('delete', id, closeDialog);
};

const basePath = '/quality-control';

const columns: QTableColumn[] = [
  {
    name: 'id',
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'permission_group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    format: (val) => val?.replace(/^[^:]*:\s*/, ''),
    sortable: true,
    align: 'center',
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  {
    name: 'created_by',
    label: 'Created by',
    align: 'center',
    field: (row) => row.created_by_username ?? null,
  },
  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];

const isSmallWindow = window.innerWidth < 1200;

const colMinWidths: Record<string, number> = {
  id: 40,
  permission_group: 40,
  name: 40,
  created_by: 60,
  action: 120,
};

const defaultColWidths: Record<string, number> = {
  id: 60,
  permission_group: isSmallWindow ? 80 : 150,
  name: isSmallWindow ? 80 : 120,
  created_by: 80,
  action: 140,
};
</script>
