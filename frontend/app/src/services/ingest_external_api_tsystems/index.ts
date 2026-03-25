import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiTSystemsPublic, IngestExternalApiTSystemsCreate, IngestExternalApiTSystemsUpdate} from "src/services/ingest_external_api_tsystems/types";
import type { PaginatedResponse } from 'src/services/types';

const apiPath = 'ingest/external-api/tsystems/';

async function getList(page?: number, size?: number) {
  
  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;
  
  return await axiosInstance.get<PaginatedResponse<IngestExternalApiTSystemsPublic>>(apiPath, {
    params,
  });
}

async function getOne(id: number){
  return await axiosInstance.get<IngestExternalApiTSystemsPublic>(`${apiPath}${id}`)
}

async function create(input: IngestExternalApiTSystemsCreate){
  return await axiosInstance.post<IngestExternalApiTSystemsPublic>(apiPath, input)
}

async function update(id:number, input: IngestExternalApiTSystemsUpdate){
  return await axiosInstance.patch<IngestExternalApiTSystemsPublic>(`${apiPath}${id}`, input)
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
