import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiTSystemsPublic, IngestExternalApiTSystemsCreate, IngestExternalApiTSystemsUpdate} from "src/services/ingest_external_api_tsystems/types";

const apiPath = 'ingest/external-api/tsystems/';

async function getList(){
  return await axiosInstance.get<IngestExternalApiTSystemsPublic[]>(apiPath)
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
