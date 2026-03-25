import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestExternalApiUbaCreate, IngestExternalApiUbaPublic, IngestExternalApiUbaUpdate} from "src/services/ingest_external_api_uba/types";
import {API} from "src/services";

export const useIngestExternalApiUbaStore = defineStore('ingestExternalApiUbaStore', {
  state: () => ({
    ingestExternalApiUbaList: [] as IngestExternalApiUbaPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList(page?: number, size?: number) {
      const response = await API.ingestExternalApiUba.getList(page, size);
      this.ingestExternalApiUbaList = response.data.items;
      return response.data;
    },
    async dispatchGetOne(id: number): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiUba.getOne(id);
      return response.data;
    },
    async dispatchCreate(payload: IngestExternalApiUbaCreate): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiUba.create(payload);
      return response.data;
    },
    async dispatchUpdate(
      id: number,
      payload: IngestExternalApiUbaUpdate,
    ): Promise<IngestExternalApiUbaPublic> {
      const response = await API.ingestExternalApiUba.update(id, payload);
      return response.data;
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestExternalApiUba.deleteOne(id);
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiUbaStore, import.meta.hot));
}
