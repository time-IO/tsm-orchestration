import {axiosInstance} from "boot/axios";

import type {PermissionGroup} from "src/services/permission_group/types";

const apiPath = "permission-group/"

async function getList(){
  return await axiosInstance.get<PermissionGroup[]>(apiPath)
}
async function getOne(id: number){
  return await axiosInstance.get<PermissionGroup>(`${apiPath}${id}`)
}

export default {
  getList,
  getOne
}
