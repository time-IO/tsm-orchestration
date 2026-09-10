import { axiosInstance } from 'src/boot/axios';
import type { TriggerSyncExtSftpBase, TriggerSyncExtSftpResponse } from './types.ts';

async function trigger_sftp(input: TriggerSyncExtSftpBase) {
  const apiPath = `/trigger/external-sftp/`;
  return await axiosInstance.post<TriggerSyncExtSftpResponse>(apiPath, input);
}

export default {
  trigger_sftp,
};
