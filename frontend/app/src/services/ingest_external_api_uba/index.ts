import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiUbaPublic, IngestExternalApiUbaCreate, IngestExternalApiUbaUpdate} from "src/services/ingest_external_api_uba/types";
import type { PaginatedResponse } from 'src/services/types';

const apiPath = "ingest/external-api/uba/"

async function getList(page?: number, size?: number) {

  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<IngestExternalApiUbaPublic>>(apiPath, {
    params,
  });
}

async function getOne(id: number){
  return await axiosInstance.get<IngestExternalApiUbaPublic>(`${apiPath}${id}`)
}

async function create(input: IngestExternalApiUbaCreate){
  return await axiosInstance.post<IngestExternalApiUbaPublic>(apiPath, input)
}

async function update(id:number, input: IngestExternalApiUbaUpdate){
  return await axiosInstance.patch<IngestExternalApiUbaPublic>(`${apiPath}${id}`, input)
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
