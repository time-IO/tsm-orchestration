import { defineStore, acceptHMRUpdate } from 'pinia';
import { API } from '@/services';
import type {
  TriggerSyncExtSftpBase,
  TriggerSyncExtSftpResponse,
} from '@/services/trigger_external_sftp/types';

export const useTriggerExternalSftpStore = defineStore('triggerExternalSftpStore', {
  state: () => ({
    provider: null,
  }),
  getters: {},

  actions: {
    async dispatchTriggerSftp(input: TriggerSyncExtSftpBase): Promise<TriggerSyncExtSftpResponse> {
      const response = await API.triggerExternalSftp.trigger_sftp(input);
      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTriggerExternalSftpStore, import.meta.hot));
}
