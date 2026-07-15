import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';
import type { PermissionGroup } from 'src/services/permission_group/types';

export const usePermissionGroupStore = defineStore('permissionGroupStore', {
  state: () => ({
    permissionGroups: [] as PermissionGroup[],
  }),

  getters: {},

  actions: {
    async dispatchGetList(page?: number, size?: number) {
      const response = await API.permissionGroup.getList(page, size);
      this.permissionGroups = response.data.items;
      return response.data;
    },
    async dispatchGetOne(id: number): Promise<PermissionGroup> {
      const response = await API.permissionGroup.getOne(id);
      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(usePermissionGroupStore, import.meta.hot));
}
