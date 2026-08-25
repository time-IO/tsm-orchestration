import type {
  PaginatedResponse,
  ParserFilter,
  QTableRequestPropPagination,
} from 'src/services/types';
import { axiosInstance } from 'boot/axios';
import type { ParserDetailedRead } from 'src/services/parser_detailed/types';

const apiPath = 'parser-detailed/';

function prepareParams(pagination: QTableRequestPropPagination, filters: ParserFilter) {
  const params: Record<string, number | string> = {};

  if (pagination.page !== undefined) params.page = pagination.page;
  if (pagination.rowsPerPage !== undefined) params.size = pagination.rowsPerPage;
  if (pagination.sortBy !== undefined) {
    const sortDirection = pagination.descending ? 'desc' : 'asc';
    params.sort_by = `${pagination.sortBy}:${sortDirection}`;
  }

  if (filters.parser_type !== undefined && filters.parser_type !== null) {
    params['parser_type[eq]'] = filters.parser_type;
  }

  if (filters.name !== undefined && filters.name !== null) {
    params['name[ilike]'] = `%${filters.name}%`;
  }
  if (filters.uuid !== undefined && filters.name !== null) {
    params['uuid[ilike]'] = `%${filters.uuid}%`;
  }
  if (filters.permission_group_id !== undefined && filters.permission_group_id !== null) {
    params['permission_group_id[eq]'] = filters.permission_group_id;
  }
  if (filters.date_from !== undefined && filters.date_from !== null) {
    params['created_at[ge]'] = filters.date_from;
  }
  if (filters.date_to !== undefined && filters.date_to !== null) {
    params['created_at[le]'] = filters.date_to;
  }

  return params;
}

async function getList(pagination: QTableRequestPropPagination, filters: ParserFilter) {
  const params = prepareParams(pagination, filters);
  return await axiosInstance.get<PaginatedResponse<ParserDetailedRead>>(apiPath, { params });
}
async function deleteOne(id: number) {
  return await axiosInstance.delete(`${apiPath}${id}`);
}

export default {
  getList,
  deleteOne,
};
