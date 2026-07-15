import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';
import type { MqttParser } from 'src/services/parser_mqtt/types';

export const useMqttParserStore = defineStore('mqttParserStore', {
  state: () => ({
    mqttParsers: [] as MqttParser[],
  }),

  getters: {},

  actions: {
    async dispatchGetList(page?: number, size?: number) {
      const response = await API.mqttParser.getList(page, size);
      this.mqttParsers = response.data.items;
      return response.data;
    },
    async dispatchGetOne(id: number): Promise<MqttParser> {
      const response = await API.mqttParser.getOne(id);
      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useMqttParserStore, import.meta.hot));
}
