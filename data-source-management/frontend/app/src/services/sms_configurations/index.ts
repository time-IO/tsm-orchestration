import { axiosInstance } from '@/boot/axios';
import type {SmsConfiguration} from "@/services/sms_configurations/types";

async function getConfigurationsByIngest(ingestId: number): Promise<SmsConfiguration[]> {
  const response = await axiosInstance.get(`ingest/${ingestId}/configurations`);
  return response.data as SmsConfiguration[]
}

export default {
  getConfigurationsByIngest,
};
