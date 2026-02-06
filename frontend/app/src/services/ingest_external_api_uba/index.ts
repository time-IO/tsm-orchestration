import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiUbaPublic, IngestExternalApiUbaCreate, IngestExternalApiUbaUpdate} from "src/services/ingest_external_api_uba/types";

const apiPath = "ingest/external-api/uba/"

async function getList(){
  return await axiosInstance.get<IngestExternalApiUbaPublic[]>(apiPath)
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
