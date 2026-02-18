import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiDwdPublic, IngestExternalApiDwdCreate, IngestExternalApiDwdUpdate} from "src/services/ingest_external_api_dwd/types";

const apiPath = "ingest/external-api/dwd/"

async function getList(){
  return await axiosInstance.get<IngestExternalApiDwdPublic[]>(apiPath)
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
