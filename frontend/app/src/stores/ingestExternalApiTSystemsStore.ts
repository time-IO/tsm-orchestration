import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestExternalApiTSystemsCreate, IngestExternalApiTSystemsPublic, IngestExternalApiTSystemsUpdate} from "src/services/ingest_external_api_tsystems/types";
import {API} from "src/services";

export const useIngestExternalApiTSystemsStore = defineStore('ingestExternalApiTSystemsStore', {

  state: () => ({
    ingestExternalApiTSystemsList: [] as IngestExternalApiTSystemsPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList() {
      const response = await API.ingestExternalApiTSystems.getList()
      this.ingestExternalApiTSystemsList = response.data
    },
    async dispatchGetOne(id: number): Promise<IngestExternalApiTSystemsPublic> {
      const response = await API.ingestExternalApiTSystems.getOne(id)
      return response.data

    },
    async dispatchCreate(payload: IngestExternalApiTSystemsCreate): Promise<IngestExternalApiTSystemsPublic> {
      const response = await API.ingestExternalApiTSystems.create(payload)
      return response.data
    },
    async dispatchUpdate(id: number, payload: IngestExternalApiTSystemsUpdate): Promise<IngestExternalApiTSystemsPublic> {
      const response = await API.ingestExternalApiTSystems.update(id, payload)
        return response.data
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestExternalApiTSystems.deleteOne(id)
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiTSystemsStore, import.meta.hot));
}
