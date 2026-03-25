import { axiosInstance } from 'src/boot/axios';
import type {
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
} from 'src/services/parser_csv/types';
import type { PaginatedResponse } from 'src/services/types';

const apiPath = 'parser/csv/';

async function getList(page?: number, size?: number) {
  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<CsvParserPublic>>(apiPath, {params});
}
async function getListbyPermissionGroup(permission_group_id: number, page?: number, size?: number) {
  const params: Record<string, number> = {};
  params.permission_group_id = permission_group_id;
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<CsvParserPublic>>(apiPath, { params });
}

async function getOne(id: number) {
  return await axiosInstance.get<CsvParserPublic>(`${apiPath}${id}`);
}

async function create(input: CsvParserCreate) {
  return await axiosInstance.post<CsvParserPublic>(apiPath, input);
}

async function update(id: number, input: CsvParserUpdate) {
  return await axiosInstance.patch<CsvParserPublic>(`${apiPath}${id}`, input);
}

async function deleteOne(id: number) {
  return await axiosInstance.delete(`${apiPath}${id}`);
}

export default {
  getList,
  getOne,
  create,
  update,
  deleteOne,
  getListbyPermissionGroup,
};
