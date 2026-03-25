import type { Ref } from 'vue';
import type { QTableRequestPropPagination } from 'src/services/types';

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
