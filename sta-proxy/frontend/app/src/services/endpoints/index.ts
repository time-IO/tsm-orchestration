import { axiosInstance } from '@/boot/axios';
import type { FrostEndpointsResponse } from '@/services/endpoints/types';

const apiPath = 'endpoints/';

async function getList(q?: string, ingestId?: number) {
  const params: Record<string, string | number> = {};
  if (q) params.q = q;
  if (ingestId !== undefined) params.ingest_id = ingestId;

  return await axiosInstance.get<FrostEndpointsResponse>(apiPath, {
    params: Object.keys(params).length ? params : undefined,
  });
}

export default {
  getList,
};
