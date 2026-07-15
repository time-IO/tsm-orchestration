import { axiosInstance } from 'boot/axios';
import type { UsageStatisticsResponse } from 'src/services/usage_statistics/types';

const apiPath = 'usage-statistics/';

async function getUsageStatistics() {
  return await axiosInstance.get<UsageStatisticsResponse>(apiPath);
}

export default {
  getUsageStatistics,
};
