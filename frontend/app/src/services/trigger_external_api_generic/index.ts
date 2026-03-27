import { axiosInstance } from 'src/boot/axios';
import type {
  TriggerSyncExtApiBase,
  TriggerSyncExtApiResponse,
} from './types.ts';




async function trigger_api_generic(provider: string, input: TriggerSyncExtApiBase) {
  const apiPath = `/trigger/external-api/${provider}`;
  return await axiosInstance.post<TriggerSyncExtApiResponse>(apiPath, input);
}

export default {
  trigger_api_generic
};
