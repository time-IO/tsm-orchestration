import {axiosInstance} from "boot/axios";

import type {NeutronMonitorStation} from "src/services/neutron_monitor_stations/type";

const apiPath = "neutron-monitor-station/"

async function getList(){
  return await axiosInstance.get<NeutronMonitorStation[]>(apiPath)
}
async function getOne(id: number){
  return await axiosInstance.get<NeutronMonitorStation>(`${apiPath}${id}`)
}

export default {
  getList,
  getOne
}
