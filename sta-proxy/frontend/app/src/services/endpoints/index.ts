import { axiosInstance } from '@/boot/axios';
import type { FrostEndpointsResponse } from '@/services/endpoints/types';

const apiPath = 'endpoints/';

async function getList(q?: string, ingest?: string) {
  const params: Record<string, string> = {};
  if (q) params.q = q;
  if (ingest) params.ingest = ingest;

  return await axiosInstance.get<FrostEndpointsResponse>(apiPath, {
    params: Object.keys(params).length ? params : undefined,
  });
}

export default {
  getList,
};
