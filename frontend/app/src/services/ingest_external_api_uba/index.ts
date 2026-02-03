import { axiosInstance } from 'src/boot/axios';
import type {IngestExternalApiUbaPublic, IngestExternalApiUbaCreate, IngestExternalApiUbaUpdate} from "src/services/ingest_external_api_uba/types";

async function getListIngestExternalApiDwd(){
  return await axiosInstance.get<IngestExternalApiUbaPublic[]>("ingest/external-api/uba/")
}

async function getOneIngestExternalApiDwd(id: number){
  return await axiosInstance.get<IngestExternalApiUbaPublic>(`ingest/external-api/uba/${id}`)
}

async function createIngestExternalApiDwd(input: IngestExternalApiUbaCreate){
  return await axiosInstance.post<IngestExternalApiUbaPublic>(`ingest/external-api/uba/`, input)
}

async function updateIngestExternalApiDwd(id:number, input: IngestExternalApiUbaUpdate){
  return await axiosInstance.patch<IngestExternalApiUbaPublic>(`ingest/external-api/uba/${id}`, input)
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
