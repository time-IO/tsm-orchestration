import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';
import type { NeutronMonitorStation } from 'src/services/neutron_monitor_stations/types';

export const useNeutronMonitorStationStore = defineStore('neutronMonitorStationStore', {
  state: () => ({}),

  getters: {},

  actions: {
    async dispatchGetList(page?: number, size?: number) {
      const response = await API.neutronMonitorStation.getList(page, size);
      return response.data;
    },
    async dispatchGetOne(id: number): Promise<NeutronMonitorStation> {
      const response = await API.neutronMonitorStation.getOne(id);
      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useNeutronMonitorStationStore, import.meta.hot));
}
