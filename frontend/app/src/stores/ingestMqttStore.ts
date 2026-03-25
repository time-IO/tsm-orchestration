import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestMqttCreate, IngestMqttPublic, IngestMqttUpdate} from "src/services/ingest_mqtt/types";
import {API} from "src/services";

export const useIngestMqttStore = defineStore('ingestMqttStore', {
  state: () => ({
    ingestMqttList: [] as IngestMqttPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList(page?: number, size?: number) {
      const response = await API.ingestMqtt.getList(page,size);
      this.ingestMqttList = response.data.items;
      return response.data
    },
    async dispatchGetOne(id: number): Promise<IngestMqttPublic> {
      const response = await API.ingestMqtt.getOne(id);
      return response.data;
    },
    async dispatchCreate(payload: IngestMqttCreate): Promise<IngestMqttPublic> {
      const response = await API.ingestMqtt.create(payload);
      return response.data;
    },
    async dispatchUpdate(id: number, payload: IngestMqttUpdate): Promise<IngestMqttPublic> {
      const response = await API.ingestMqtt.update(id, payload);
      return response.data;
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestMqtt.deleteOne(id);
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestMqttStore, import.meta.hot));
}
