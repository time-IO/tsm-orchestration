import {axiosInstance} from "boot/axios";
import type {MqttParser} from "src/services/mqtt_parser/type";


const apiPath = "mqtt-parser/"

async function getList(){
  return await axiosInstance.get<MqttParser[]>(apiPath)
}
async function getOne(id: number){
  return await axiosInstance.get<MqttParser>(`${apiPath}${id}`)
}

export default {
  getList,
  getOne
}
