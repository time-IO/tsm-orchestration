import {API} from "src/services";
import {acceptHMRUpdate, defineStore} from "pinia";
import type {MqttParser} from "src/services/mqtt_parser/type";


export const useMqttParserStore = defineStore('mqttParserStore', {

  state: () => ({
    mqttParsers: [] as MqttParser[]
  }),

  getters:{},

  actions: {
    async dispatchGetList(){
      const response = await API.mqttParser.getList()
      this.mqttParsers = response.data
    },
    async dispatchGetOne(id:number):Promise<MqttParser> {
      const response = await API.mqttParser.getOne(id)
      return response.data
    }
  }
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useMqttParserStore, import.meta.hot));
}
