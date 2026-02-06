import {axiosInstance} from "boot/axios";

import type {Project} from "src/services/project/types";

async function getListProject(){
  return await axiosInstance.get<Project[]>("projects/")
}
async function getOneProject(id: number){
  return await axiosInstance.get<Project[]>(`projects/${id}`)
}

export default {
  getListProject,
  getOneProject
}
