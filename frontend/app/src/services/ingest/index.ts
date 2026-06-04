import { axiosInstance } from 'boot/axios';
import type {
  IngestFilter,
  PaginatedResponse,
  QTableRequestPropPagination,
} from 'src/services/types';
import type { IngestWithApiInfoRead } from 'src/services/ingest/types';

const apiPath = 'ingest/';

function prepareParams(pagination: QTableRequestPropPagination, filters: IngestFilter) {
  const params: Record<string, number | string> = {};

  if (pagination.page !== undefined) params.page = pagination.page;
  if (pagination.rowsPerPage !== undefined) params.size = pagination.rowsPerPage;
  if (pagination.sortBy !== undefined) {
    const sortDirection = pagination.descending ? 'desc' : 'asc';
    params.sort_by = `${pagination.sortBy}:${sortDirection}`;
  }

  if (filters.ingest_type !== undefined && filters.ingest_type !== null) {
    params['ingest_type[eq]'] = filters.ingest_type;
  }

  if (filters.name !== undefined && filters.name !== null) {
    params['name[ilike]'] = `%${filters.name}%`;
  }
  if (filters.uuid !== undefined && filters.uuid !== null) {
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

async function getList(pagination: QTableRequestPropPagination, filters: IngestFilter) {
  const params = prepareParams(pagination, filters);
  return await axiosInstance.get<PaginatedResponse<IngestWithApiInfoRead>>(apiPath, { params });
}
async function deleteOne(id: number) {
  return await axiosInstance.delete(`${apiPath}${id}`);
}

export default { getList, deleteOne };
