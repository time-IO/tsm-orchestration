import { axiosInstance } from 'src/boot/axios';
import type {
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschUpdate,
} from 'src/services/ingest_external_api_bosch/types';
import type { PaginatedResponse } from 'src/services/types';

const apiPath = 'ingest/external-api/bosch/';

async function getList(page?: number, size?: number) {

  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<IngestExternalApiBoschPublic>>(apiPath, {
    params,
  });
}

async function getOne(id: number) {
  return await axiosInstance.get<IngestExternalApiBoschPublic>(`${apiPath}${id}`);
}

async function create(input: IngestExternalApiBoschCreate) {
  return await axiosInstance.post<IngestExternalApiBoschPublic>(apiPath, input);
}

async function update(id: number, input: IngestExternalApiBoschUpdate) {
  return await axiosInstance.patch<IngestExternalApiBoschPublic>(`${apiPath}${id}`, input);
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
};
