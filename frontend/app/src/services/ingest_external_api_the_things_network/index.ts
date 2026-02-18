import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiTheThingsNetworkPublic, IngestExternalApiTheThingsNetworkCreate, IngestExternalApiTheThingsNetworkUpdate} from "src/services/ingest_external_api_the_things_network/types";

const apiPath = 'ingest/external-api/the-things-network/';

async function getList(){
  return await axiosInstance.get<IngestExternalApiTheThingsNetworkPublic[]>(apiPath)
}

async function getOne(id: number){
  return await axiosInstance.get<IngestExternalApiTheThingsNetworkPublic>(`${apiPath}${id}`)
}

async function create(input: IngestExternalApiTheThingsNetworkCreate){
  return await axiosInstance.post<IngestExternalApiTheThingsNetworkPublic>(apiPath, input)
}

async function update(id:number, input: IngestExternalApiTheThingsNetworkUpdate){
  return await axiosInstance.patch<IngestExternalApiTheThingsNetworkPublic>(`${apiPath}${id}`, input)
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
