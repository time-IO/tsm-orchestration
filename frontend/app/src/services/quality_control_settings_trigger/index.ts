import { axiosInstance } from 'src/boot/axios';
import type { TriggerQCSBase, TriggerQCSResponse } from './types.ts';

async function trigger_settings(input: TriggerQCSBase) {
  const triggerPath = '/trigger/quality_control/';
  return await axiosInstance.post<TriggerQCSResponse>(triggerPath, input);
}

export default {
  trigger_settings,
};
