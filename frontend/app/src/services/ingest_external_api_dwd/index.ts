import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiDwdPublic, IngestExternalApiDwdCreate, IngestExternalApiDwdUpdate} from "src/services/ingest_external_api_dwd/types";
import type { PaginatedResponse } from 'src/services/types';

const apiPath = "ingest/external-api/dwd/"

async function getList(page?: number, size?: number) {

  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<IngestExternalApiDwdPublic>>(apiPath, {
    params,
  });
}

async function getOne(id: number){
  return await axiosInstance.get<IngestExternalApiDwdPublic>(`${apiPath}${id}`)
}

async function create(input: IngestExternalApiDwdCreate){
  return await axiosInstance.post<IngestExternalApiDwdPublic>(apiPath, input)
}

async function update(id:number, input: IngestExternalApiDwdUpdate){
  return await axiosInstance.patch<IngestExternalApiDwdPublic>(`${apiPath}${id}`, input)
}

async function deleteOne(id: number){
  return await axiosInstance.delete(`${apiPath}${id}`)
}

export default {
  getList,
  getOne,
  create,
  update,
  deleteOne
}
