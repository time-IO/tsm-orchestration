import { axiosInstance } from 'src/boot/axios';
import type {
  IngestSftpPublic,
  IngestSftpCreate,
  IngestSftpUpdate,
} from 'src/services/ingest_sftp/types';

const apiPath = 'ingest/s3store/';

async function getList() {
  return await axiosInstance.get<IngestSftpPublic[]>(apiPath);
}

async function getOne(id: number) {
  return await axiosInstance.get<IngestSftpPublic>(`${apiPath}${id}`);
}

async function create(input: IngestSftpCreate) {
  return await axiosInstance.post<IngestSftpPublic>(apiPath, input);
}

async function update(id: number, input: IngestSftpUpdate) {
  return await axiosInstance.patch<IngestSftpPublic>(`${apiPath}${id}`, input);
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
