import { axiosInstance } from 'boot/axios';

import type { NeutronMonitorStation } from '@/services/neutron_monitor_stations/types';
import type { PaginatedResponse } from '@/services/types';

const apiPath = 'neutron-monitor-station/';

async function getList(page?: number, size?: number) {
  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<NeutronMonitorStation>>(apiPath, {
    params,
  });
}
async function getOne(id: number) {
  return await axiosInstance.get<NeutronMonitorStation>(`${apiPath}${id}`);
}

export default {
  getList,
  getOne,
};
