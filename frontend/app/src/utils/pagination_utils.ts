import type { Ref } from 'vue';
import type { QTableRequestPropPagination } from 'src/services/types';
import type { QTableColumn } from 'quasar';

export const defaultPagination: QTableRequestPropPagination = {
  sortBy: 'name',
  descending: false,
  page: 1,
  rowsPerPage: 25,
  rowsNumber: 0,
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
  {
    name: 'created_at',
    label: 'Created at',
    field: 'created_at',
    sortable: true,
    align: 'center',
    format: (val) => {
      if (!val) return '';
      const date = new Date(val);
      const day = String(date.getUTCDate()).padStart(2, '0');
      const month = String(date.getUTCMonth() + 1).padStart(2, '0');
      const year = date.getUTCFullYear();
      return `${day}.${month}.${year}`;
    },
  },
  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];
