import type { Ref } from 'vue';
import type { QTableRequestPropPagination } from 'src/services/types';
import type { QTableColumn } from 'quasar';

export const defaultPagination: QTableRequestPropPagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 25,
  rowsNumber: 10,
};

export function updatePagination(
  paginationToUpdate: Ref<QTableRequestPropPagination>,
  updatedInfo: { size: number; page: number; total: number },
) {
  paginationToUpdate.value.rowsPerPage = updatedInfo.size;
  paginationToUpdate.value.page = updatedInfo.page;
  paginationToUpdate.value.rowsNumber = updatedInfo.total;
}

export const default_ingest_columns: QTableColumn[] = [
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
