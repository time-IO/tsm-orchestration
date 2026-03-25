import { defineStore, acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschUpdate,
} from 'src/services/ingest_external_api_bosch/types';
import { API } from 'src/services';

export const useIngestExternalApiBoschStore = defineStore('ingestExternalApiBoschStore', {
  state: () => ({
    ingestExternalApiBoschList: [] as IngestExternalApiBoschPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList(page?: number, size?: number) {
      const response = await API.ingestExternalApiBosch.getList(page, size);
      this.ingestExternalApiBoschList = response.data.items;
      return response.data;
    },
    async dispatchGetOne(id: number): Promise<IngestExternalApiBoschPublic> {
      const response = await API.ingestExternalApiBosch.getOne(id);
      return response.data;
    },
    async dispatchCreate(
      payload: IngestExternalApiBoschCreate,
    ): Promise<IngestExternalApiBoschPublic> {
      const response = await API.ingestExternalApiBosch.create(payload);
      return response.data;
    },
    async dispatchUpdate(
      id: number,
      payload: IngestExternalApiBoschUpdate,
    ): Promise<IngestExternalApiBoschPublic> {
      const response = await API.ingestExternalApiBosch.update(id, payload);
      return response.data;
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestExternalApiBosch.deleteOne(id);
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiBoschStore, import.meta.hot));
}
