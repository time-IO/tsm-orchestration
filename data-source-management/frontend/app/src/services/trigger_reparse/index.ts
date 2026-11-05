import { axiosInstance } from '@/boot/axios';
import type {TriggerReparseBase, TriggerReparseResponse} from "./types";

async function trigger_reparse(input: TriggerReparseBase){
  const apiPath = '/trigger/reparse/';
  return await axiosInstance.post<TriggerReparseResponse>(apiPath, input);
}

export default {
  trigger_reparse,
};
