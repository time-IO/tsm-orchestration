import { axiosInstance } from '@/boot/axios';

const apiPath = '/ingest/';

async function getDatabaseName(id: number): Promise<string> {
  const response = await axiosInstance.get<string>(`${apiPath}${id}/database`);
  return response.data;
}

export default {
  getDatabaseName,
};
