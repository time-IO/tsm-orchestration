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
    async dispatchGetListIngestExternalApiDwd() {
      const response = await API.ingestExternalApiDwd.getListIngestExternalApiDwd()
      this.ingestExternalApiUbaList = response.data
    },
    async dispatchGetOneIngestExternalApiDwd(id: number): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiDwd.getOneIngestExternalApiDwd(id)
      return response.data

    },
    async dispatchCreateIngestExternalApiDwd(payload: IngestExternalApiUbaCreate): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiDwd.createIngestExternalApiDwd(payload)
      return response.data

    },
    async dispatchUpdateIngestExternalApiDwd(id: number, payload: IngestExternalApiUbaUpdate): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiDwd.updateIngestExternalApiDwd(id, payload)
        return response.data
    },
    async dispatchDeleteIngestExternalApiDwd(id: number): Promise<void> {
      await API.ingestExternalApiDwd.deleteIngestExternalApiDwd(id)
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiUbaStore, import.meta.hot));
}
