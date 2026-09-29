<template>
  <overview-table-base
    v-model:pagination="pagination"
    :rows="rows"
    :loading="loading"
    :columns="columns"
    storage-key="qcsetting"
    @on-request="emit('onRequest', $event)"
  >
    <template #action="{ row }">
      <q-btn :to="`${basePath}/${row.id}`" flat outline color="primary" icon="visibility">
        <q-tooltip>View details</q-tooltip>
      </q-btn>
      <q-btn :to="`${basePath}/${row.id}/edit`" flat outline color="secondary" icon="edit">
        <q-tooltip>Edit</q-tooltip>
      </q-btn>
      <q-btn :to="`${basePath}/${row.id}/copy`" flat outline color="black" icon="content_copy">
        <q-tooltip>Copy</q-tooltip>
      </q-btn>
      <q-btn flat outline color="negative" icon="delete" @click="emit('delete', row.id)">
        <q-tooltip>Delete</q-tooltip>
      </q-btn>
    </template>
  </overview-table-base>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import type { QTableRequestPropPagination } from '@/services/types';
import OverviewTableBase from "@/components/OverviewTableBase.vue";

defineProps<{ rows: unknown[]; loading: boolean }>();
const pagination = defineModel<QTableRequestPropPagination | undefined>('pagination');
const emit = defineEmits(['onRequest', 'delete']);

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
</script>
