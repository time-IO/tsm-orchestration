import { defineStore, acceptHMRUpdate } from 'pinia';
import { API } from 'src/services';
import type {
  TriggerQCSBase,
  TriggerQCSResponse,
} from 'src/services/quality_control_settings_trigger/types';

export const useTriggerQCSStore = defineStore('triggerQCSStore', {
  state: () => ({}),
  getters: {},

  actions: {
    async dispatchTriggerSetting(input: TriggerQCSBase): Promise<TriggerQCSResponse> {
      const response = await API.triggerQCSetting.trigger_settings(input);
      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTriggerQCSStore, import.meta.hot));
}
