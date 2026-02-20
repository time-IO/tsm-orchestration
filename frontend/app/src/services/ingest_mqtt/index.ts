import { axiosInstance } from 'src/boot/axios';
import type {IngestMqttPublic, IngestMqttCreate, IngestMqttUpdate} from "src/services/ingest_mqtt/types";

const apiPath = "ingest/mqtt/"

async function getList(){
  return await axiosInstance.get<IngestMqttPublic[]>(apiPath)
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
