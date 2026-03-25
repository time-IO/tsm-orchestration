import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestExternalApiNeutronMonitorCreate, IngestExternalApiNeutronMonitorPublic, IngestExternalApiNeutronMonitorUpdate} from "src/services/ingest_external_api_neutron_monitor/types";
import {API} from "src/services";

export const useIngestExternalApiNeutronMonitorStore = defineStore(
  'ingestExternalApiNeutronMonitorStore',
  {
    state: () => ({
      ingestExternalApiNeutronMonitorList: [] as IngestExternalApiNeutronMonitorPublic[],
    }),

    getters: {},

    actions: {
      async dispatchGetList(page?: number, size?: number) {
        const response = await API.ingestExternalApiNeutronMonitor.getList(page, size);
        this.ingestExternalApiNeutronMonitorList = response.data.items;
        return response.data;
      },
      async dispatchGetOne(id: number): Promise<IngestExternalApiNeutronMonitorPublic> {
        const response = await API.ingestExternalApiNeutronMonitor.getOne(id);
        return response.data;
      },
      async dispatchCreate(
        payload: IngestExternalApiNeutronMonitorCreate,
      ): Promise<IngestExternalApiNeutronMonitorPublic> {
        const response = await API.ingestExternalApiNeutronMonitor.create(payload);
        return response.data;
      },
      async dispatchUpdate(
        id: number,
        payload: IngestExternalApiNeutronMonitorUpdate,
      ): Promise<IngestExternalApiNeutronMonitorPublic> {
        const response = await API.ingestExternalApiNeutronMonitor.update(id, payload);
        return response.data;
      },
      async dispatchDelete(id: number): Promise<void> {
        await API.ingestExternalApiNeutronMonitor.deleteOne(id);
      },
    },
  },
);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiNeutronMonitorStore, import.meta.hot));
}
