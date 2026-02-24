import { axiosInstance } from 'src/boot/axios';
import type {
  IngestExternalSftpPublic,
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate,
} from 'src/services/ingest_external_sftp/types';

const apiPath = 'ingest/external-sftp/';

async function getList() {
  return await axiosInstance.get<IngestExternalSftpPublic[]>(apiPath);
}

async function getOne(id: number) {
  return await axiosInstance.get<IngestExternalSftpPublic>(`${apiPath}${id}`);
}

async function create(input: IngestExternalSftpCreate) {
  return await axiosInstance.post<IngestExternalSftpPublic>(apiPath, input);
}

async function update(id: number, input: IngestExternalSftpUpdate) {
  return await axiosInstance.patch<IngestExternalSftpPublic>(`${apiPath}${id}`, input);
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
