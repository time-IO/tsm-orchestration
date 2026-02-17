import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiNeutronMonitorPublic, IngestExternalApiNeutronMonitorCreate, IngestExternalApiNeutronMonitorUpdate} from "src/services/ingest_external_api_neutron_monitor/types";

const apiPath = "ingest/external-api/neutron-monitor/"

async function getList(){
  return await axiosInstance.get<IngestExternalApiNeutronMonitorPublic[]>(apiPath)
}

async function getOne(id: number){
  return await axiosInstance.get<IngestExternalApiNeutronMonitorPublic>(`${apiPath}${id}`)
}

async function create(input: IngestExternalApiNeutronMonitorCreate){
  return await axiosInstance.post<IngestExternalApiNeutronMonitorPublic>(apiPath, input)
}

async function update(id:number, input: IngestExternalApiNeutronMonitorUpdate){
  return await axiosInstance.patch<IngestExternalApiNeutronMonitorPublic>(`${apiPath}${id}`, input)
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
