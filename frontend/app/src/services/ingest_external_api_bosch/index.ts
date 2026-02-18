import { axiosInstance } from 'src/boot/axios';
import type {
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschUpdate,
} from 'src/services/ingest_external_api_bosch/types';

const apiPath = 'ingest/external-api/bosch/';

async function getList() {
  return await axiosInstance.get<IngestExternalApiBoschPublic[]>(apiPath);
}

async function getOne(id: number) {
  return await axiosInstance.get<IngestExternalApiBoschPublic>(`${apiPath}${id}`);
}

async function create(input: IngestExternalApiBoschCreate) {
  return await axiosInstance.post<IngestExternalApiBoschPublic>(apiPath, input);
}

async function update(id: number, input: IngestExternalApiBoschUpdate) {
  return await axiosInstance.patch<IngestExternalApiBoschPublic>(`${apiPath}${id}`, input);
}

async function deleteOne(id: number) {
  return await axiosInstance.delete(`${apiPath}${id}`);
}

export default {
  getList,
  getOne,
  create,
  update,
  deleteOne,
};
