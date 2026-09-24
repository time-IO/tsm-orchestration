import { axiosInstance } from '@/boot/axios';
import type { FrostEndpointsResponse } from '@/services/endpoints/types';

const apiPath = 'endpoints/';

async function getList(q?: string) {
  return await axiosInstance.get<FrostEndpointsResponse>(apiPath, {
    params: q ? { q } : undefined,
  });
}

export default {
  getList,
};
