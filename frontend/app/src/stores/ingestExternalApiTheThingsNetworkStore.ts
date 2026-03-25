import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestExternalApiTheThingsNetworkCreate, IngestExternalApiTheThingsNetworkPublic, IngestExternalApiTheThingsNetworkUpdate} from "src/services/ingest_external_api_the_things_network/types";
import {API} from "src/services";

export const useIngestExternalApiTheThingsNetworkStore = defineStore(
  'ingestExternalApiTheThingsNetworkStore',
  {
    state: () => ({
      ingestExternalApiTheThingsNetworkList: [] as IngestExternalApiTheThingsNetworkPublic[],
    }),

    getters: {},

    actions: {
      async dispatchGetList(page?: number, size?: number) {
        const response = await API.ingestExternalApiTheThingsNetwork.getList(page, size);
        this.ingestExternalApiTheThingsNetworkList = response.data.items;
        return response.data;
      },
      async dispatchGetOne(id: number): Promise<IngestExternalApiTheThingsNetworkPublic> {
        const response = await API.ingestExternalApiTheThingsNetwork.getOne(id);
        return response.data;
      },
      async dispatchCreate(
        payload: IngestExternalApiTheThingsNetworkCreate,
      ): Promise<IngestExternalApiTheThingsNetworkPublic> {
        const response = await API.ingestExternalApiTheThingsNetwork.create(payload);
        return response.data;
      },
      async dispatchUpdate(
        id: number,
        payload: IngestExternalApiTheThingsNetworkUpdate,
      ): Promise<IngestExternalApiTheThingsNetworkPublic> {
        const response = await API.ingestExternalApiTheThingsNetwork.update(id, payload);
        return response.data;
      },
      async dispatchDelete(id: number): Promise<void> {
        await API.ingestExternalApiTheThingsNetwork.deleteOne(id);
      },
    },
  },
);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiTheThingsNetworkStore, import.meta.hot));
}
