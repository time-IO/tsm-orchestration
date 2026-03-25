import { axiosInstance } from 'src/boot/axios';
import type {IngestMqttPublic, IngestMqttCreate, IngestMqttUpdate} from "src/services/ingest_mqtt/types";
import type { PaginatedResponse } from 'src/services/types';

const apiPath = "ingest/mqtt/"

async function getList(page?: number, size?: number) {

  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<IngestMqttPublic>>(apiPath, {
    params,
  });
}

async function getOne(id: number){
  return await axiosInstance.get<IngestMqttPublic>(`${apiPath}${id}`)
}

async function create(input: IngestMqttCreate){
  return await axiosInstance.post<IngestMqttPublic>(apiPath, input)
}

async function update(id:number, input: IngestMqttUpdate){
  return await axiosInstance.patch<IngestMqttPublic>(`${apiPath}${id}`, input)
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
