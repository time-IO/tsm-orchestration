import {API} from "src/services";
import {acceptHMRUpdate, defineStore} from "pinia";
import type {PermissionGroup} from "src/services/permission_group/types";

export const usePermissionGroupStore = defineStore('permissionGroupStore', {

  state: () => ({
    permissionGroups: [] as PermissionGroup[]
  }),

  getters:{},

  actions: {
    async dispatchGetList(){
      const response = await API.permissionGroup.getList()
      this.permissionGroups = response.data
    },
    async dispatchGetOne(id:number):Promise<PermissionGroup> {
      const response = await API.permissionGroup.getOne(id)
      return response.data
    }
  }
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(usePermissionGroupStore, import.meta.hot));
}
