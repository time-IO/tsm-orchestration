import { defineStore, acceptHMRUpdate } from 'pinia';
import { API } from '@/services';
import type {
  TriggerReparseBase,
  TriggerReparseResponse,
} from '@/services/trigger_reparse/types';

export const useTriggerReparseStore = defineStore('triggerReparseStore',{
  state: () => ({}),
  getters: {},

  actions: {
    async dispatchTriggerReparse(input: TriggerReparseBase): Promise<TriggerReparseResponse> {
      const response = await API.triggerReparse.trigger_reparse(input);
      return response.data
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTriggerReparseStore, import.meta.hot));
}
