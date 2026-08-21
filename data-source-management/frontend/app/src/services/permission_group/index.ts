import { axiosInstance } from 'boot/axios';
import type { PaginatedResponse } from 'src/services/types';
import type { PermissionGroup } from 'src/services/permission_group/types';

const apiPath = 'permission-group/';

async function getList(page?: number, size?: number) {
  const params: Record<string, number | string> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;
  params.sort_by = 'name:asc';

  return await axiosInstance.get<PaginatedResponse<PermissionGroup>>(apiPath, { params });
}
async function getOne(id: number) {
  return await axiosInstance.get<PermissionGroup>(`${apiPath}${id}`);
}

export default {
  getList,
  getOne,
};
