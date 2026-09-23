import { axiosInstance } from '@/boot/axios';
import type { FrostEndpointsResponse } from '@/services/endpoints/types';

const apiPath = 'endpoints/';

async function getList() {
  return await axiosInstance.get<FrostEndpointsResponse>(apiPath);
}

export default {
  getList,
};
