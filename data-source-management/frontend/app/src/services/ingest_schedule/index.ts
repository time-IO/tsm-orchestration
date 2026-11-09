import { axiosInstance } from '@/boot/axios';
import type {
  CustomJob,
  CustomJobInput,
  CustomJobSpec,
  IngestScheduleInfo,
} from '@/services/ingest_schedule/types';

const apiPath = '/ingest/';

async function getSchedule(ingestId: number): Promise<IngestScheduleInfo> {
  const response = await axiosInstance.get<IngestScheduleInfo>(`${apiPath}${ingestId}/schedule`);
  return response.data;
}

async function getAvailableCustomJobs(ingestId: number): Promise<CustomJobSpec[]> {
  const response = await axiosInstance.get<CustomJobSpec[]>(
    `${apiPath}${ingestId}/custom-jobs/available`,
  );
  return response.data;
}

async function createCustomJob(ingestId: number, input: CustomJobInput): Promise<CustomJob> {
  const response = await axiosInstance.post<CustomJob>(`${apiPath}${ingestId}/custom-jobs`, input);
  return response.data;
}

async function updateCustomJob(
  ingestId: number,
  jobId: number,
  input: Partial<CustomJobInput>,
): Promise<CustomJob> {
  const response = await axiosInstance.patch<CustomJob>(
    `${apiPath}${ingestId}/custom-jobs/${jobId}`,
    input,
  );
  return response.data;
}

async function deleteCustomJob(ingestId: number, jobId: number): Promise<void> {
  await axiosInstance.delete(`${apiPath}${ingestId}/custom-jobs/${jobId}`);
}

export default {
  getSchedule,
  getAvailableCustomJobs,
  createCustomJob,
  updateCustomJob,
  deleteCustomJob,
};
