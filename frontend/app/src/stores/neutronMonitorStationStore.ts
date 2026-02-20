import {API} from "src/services";
import {acceptHMRUpdate, defineStore} from "pinia";
import type {NeutronMonitorStation} from "src/services/neutron_monitor_stations/type";


export const useNeutronMonitorStationStore = defineStore('neutronMonitorStationStore', {

  state: () => ({
    neutronMonitorStations: [] as NeutronMonitorStation[]
  }),

  getters:{},

  actions: {
    async dispatchGetList(){
      const response = await API.neutronMonitorStation.getList()
      this.neutronMonitorStations = response.data
    },
    async dispatchGetOne(id:number):Promise<NeutronMonitorStation> {
      const response = await API.neutronMonitorStation.getOne(id)
      return response.data
    }
  }
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useNeutronMonitorStationStore, import.meta.hot));
}
