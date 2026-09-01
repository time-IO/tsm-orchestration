import type {
  DefaultFilter,
  PaginatedResponse,
  QTableRequestPropPagination,
} from 'src/services/types';
import { axiosInstance } from 'boot/axios';

export function createIngestApiService<TPublic, TCreate, TUpdate>(apiPath: string) {
  function prepareParams(pagination: QTableRequestPropPagination, filters: DefaultFilter) {
    const params: Record<string, number | string> = {};

    if (pagination.page !== undefined) params.page = pagination.page;
    if (pagination.rowsPerPage !== undefined) params.size = pagination.rowsPerPage;
    if (pagination.sortBy !== undefined) {
      const sortDirection = pagination.descending ? 'desc' : 'asc';
      params.sort_by = `${pagination.sortBy}:${sortDirection}`;
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
    if (
      filters.functions !== undefined &&
      filters.functions !== null &&
      filters.functions.length > 0
    ) {
      params['functions[overlap]'] = filters.functions.join(',');
    }

    return params;
  }

  async function getList(pagination: QTableRequestPropPagination, filters: DefaultFilter) {
    const params = prepareParams(pagination, filters);
    return await axiosInstance.get<PaginatedResponse<TPublic>>(apiPath, { params });
  }

  async function getOne(id: number) {
    return await axiosInstance.get<TPublic>(`${apiPath}${id}`);
  }

  async function create(input: TCreate) {
    return await axiosInstance.post<TPublic>(apiPath, input);
  }

  async function update(id: number, input: TUpdate) {
    return await axiosInstance.patch<TPublic>(`${apiPath}${id}`, input);
  }

  async function deleteOne(id: number) {
    return await axiosInstance.delete(`${apiPath}${id}`);
  }

  return {
    getList,
    getOne,
    create,
    update,
    deleteOne,
  };
}
