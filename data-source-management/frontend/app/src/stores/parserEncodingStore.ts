import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';
import type { ParserEncoding } from 'src/services/parser_encoding/types';

export const useParserEncodingStore = defineStore('parserEncodingStore', {
  state: () => ({
    rows: [] as ParserEncoding[],
  }),
  getters: {},
  actions: {
    async dispatchGetList() {
      const response = await API.parserEncoding.getList();
      this.rows = response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useParserEncodingStore, import.meta.hot));
}
