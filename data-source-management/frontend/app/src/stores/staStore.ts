import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';
import type { StaDatastreamRequestParameter } from 'src/services/sta/types';

export const useStaStore = defineStore('staStore', {
  state: () => ({
    datastreams: [],
  }),

  getters: {},

  actions: {
    async dispatchFetchDatastreams(
      permission_group_id: number,
      parameter: StaDatastreamRequestParameter,
    ) {
      const response = await API.sta.fetchDatastreams(permission_group_id, parameter);

      return response.data;
    },
    async dispatchFetchThings(permission_group_id: number, search: string) {
      const response = await API.sta.fetchThings(permission_group_id, search);

      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useStaStore, import.meta.hot));
}
