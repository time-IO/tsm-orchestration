import {axiosInstance} from "boot/axios";

import type {Project} from "src/services/project/types";

const apiPath = "ingest/external-api/uba/"

async function getList(){
  return await axiosInstance.get<Project[]>(apiPath)
}
async function getOne(id: number){
  return await axiosInstance.get<Project>(`${apiPath}${id}`)
}

export default {
  getList,
  getOne
}
