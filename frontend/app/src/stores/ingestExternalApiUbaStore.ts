import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestExternalApiUbaCreate, IngestExternalApiUbaPublic, IngestExternalApiUbaUpdate} from "src/services/ingest_external_api_uba/types";
import {API} from "src/services";

export const useIngestExternalApiUbaStore = defineStore('ingestExternalApiUbaStore', {

  state: () => ({
    ingestExternalApiUbaList: [] as IngestExternalApiUbaPublic[],
    ingestExternalApiUba: null as IngestExternalApiUbaPublic | null, // todo not 100% sure if I'll go with this
  }),

  getters: {},

  actions: {
    async dispatchGetList() {
      const response = await API.ingestExternalApiDwd.getList()
      this.ingestExternalApiUbaList = response.data
    },
    async dispatchGetOne(id: number): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiDwd.getOne(id)
      return response.data

    },
    async dispatchCreate(payload: IngestExternalApiUbaCreate): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiDwd.create(payload)
      return response.data
    },
    async dispatchUpdate(id: number, payload: IngestExternalApiUbaUpdate): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiDwd.update(id, payload)
        return response.data
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestExternalApiDwd.deleteOne(id)
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiUbaStore, import.meta.hot));
}
