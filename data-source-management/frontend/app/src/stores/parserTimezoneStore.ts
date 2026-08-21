import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';

export const useParserTimezoneStore = defineStore('parserTimezoneStore', {
  state: () => ({
    rows: [] as string[],
  }),
  getters: {},
  actions: {
    async dispatchGetList() {
      const response = await API.parserTimezone.getList();
      this.rows = response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useParserTimezoneStore, import.meta.hot));
}
