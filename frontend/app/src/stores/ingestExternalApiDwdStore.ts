import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestExternalApiDwdCreate, IngestExternalApiDwdPublic, IngestExternalApiDwdUpdate} from "src/services/ingest_external_api_dwd/types";
import {API} from "src/services";

export const useIngestExternalApiDwdStore = defineStore('ingestExternalApiDwdStore', {

  state: () => ({
    ingestExternalApiDwdList: [] as IngestExternalApiDwdPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList() {
      const response = await API.ingestExternalApiDwd.getList()
      this.ingestExternalApiDwdList = response.data
    },
    async dispatchGetOne(id: number): Promise<IngestExternalApiDwdPublic> {
      const response = await API.ingestExternalApiDwd.getOne(id)
      return response.data

    },
    async dispatchCreate(payload: IngestExternalApiDwdCreate): Promise<IngestExternalApiDwdPublic> {
      const response = await API.ingestExternalApiDwd.create(payload)
      return response.data
    },
    async dispatchUpdate(id: number, payload: IngestExternalApiDwdUpdate): Promise<IngestExternalApiDwdPublic> {
      const response = await API.ingestExternalApiDwd.update(id, payload)
        return response.data
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestExternalApiDwd.deleteOne(id)
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiDwdStore, import.meta.hot));
}
