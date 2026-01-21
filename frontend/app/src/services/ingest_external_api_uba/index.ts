import { axiosInstance } from 'src/boot/axios';
import {IngestExternalApiUbaPublic, IngestExternalApiUbaCreate, IngestExternalApiUbaUpdate} from "src/services/ingest_external_api_uba/types";
import {AxiosResponse} from "axios";

async function getListIngestExternalApiDwd(){
  return await axiosInstance.get<AxiosResponse<IngestExternalApiUbaPublic[]>>("ingest/external-api/uba/")
}

async function getOneIngestExternalApiDwd(id: number){
  return await axiosInstance.get<AxiosResponse<IngestExternalApiUbaPublic>>(`ingest/external-api/uba/${id}`)
}

async function createIngestExternalApiDwd(input: IngestExternalApiUbaCreate){
  return await axiosInstance.post<AxiosResponse<IngestExternalApiUbaPublic>>(`ingest/external-api/uba/`, input)
}

async function updateIngestExternalApiDwd(id:number, input: IngestExternalApiUbaUpdate){
  return await axiosInstance.patch<AxiosResponse<IngestExternalApiUbaPublic>>(`ingest/external-api/uba/${id}`, input)
}

async function deleteIngestExternalApiDwd(id: number){
  return await axiosInstance.delete(`ingest/external-api/uba/${id}`)
}

export default {
  getListIngestExternalApiDwd,
  getOneIngestExternalApiDwd,
  createIngestExternalApiDwd,
  updateIngestExternalApiDwd,
  deleteIngestExternalApiDwd
}
