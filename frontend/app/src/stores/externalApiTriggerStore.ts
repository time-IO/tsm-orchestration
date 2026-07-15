import { defineStore, acceptHMRUpdate } from 'pinia';
import { API } from 'src/services';
import type {
  TriggerSyncExtApiBase,
  TriggerSyncExtApiResponse,
} from 'src/services/trigger_external_api_generic/types';

export const useTriggerExternalGenericApiStore = defineStore('triggerExternalApiStore', {
  state: () => ({
    provider: null,
  }),
  getters: {},

  actions: {
    async dispatchTriggerApi(input: TriggerSyncExtApiBase): Promise<TriggerSyncExtApiResponse> {
      const response = await API.triggerExternalGenAPI.trigger_api_generic(input);
      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTriggerExternalGenericApiStore, import.meta.hot));
}
