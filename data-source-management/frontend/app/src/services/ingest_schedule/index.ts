import { axiosInstance } from '@/boot/axios';
import type { IngestScheduleInfo } from '@/services/ingest_schedule/types';

const apiPath = '/ingest/';

async function getSchedule(ingestId: number): Promise<IngestScheduleInfo> {
  const response = await axiosInstance.get<IngestScheduleInfo>(`${apiPath}${ingestId}/schedule`);
  return response.data;
}

export default {
  getSchedule,
};
