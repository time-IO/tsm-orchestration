import { axiosInstance } from 'src/boot/axios';
import type {
  IngestSftpPublic,
  IngestSftpCreate,
  IngestSftpUpdate,
} from 'src/services/ingest_sftp/types';
import type { PaginatedResponse } from 'src/services/types';

const apiPath = 'ingest/s3store/';

async function getList(page?: number, size?: number) {

  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<IngestSftpPublic>>(apiPath, {
    params,
  });
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
