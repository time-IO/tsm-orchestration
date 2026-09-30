import { axiosInstance } from '@/boot/axios';
import type { IngestsResponse } from '@/services/ingests/types';

const apiPath = 'ingests/';

async function search(q?: string) {
  return await axiosInstance.get<IngestsResponse>(apiPath, {
    params: q ? { q } : undefined,
  });
}

export default {
  search,
};
