import {defineStore, acceptHMRUpdate} from 'pinia';
import type {
  CsvParserCreate,
  CsvParserPublic,
  CsvParserTimestampColumnPublic,
  CsvParserTimestampColumnUpdate,
  CsvParserUpdate,
} from 'src/services/parser_csv/types';
import {API} from "src/services";

export const useCsvParserStore = defineStore('csvParserStore', {
  state: () => ({
    csvParserList: [] as CsvParserPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList() {
      const response = await API.csvParser.getList();
      this.csvParserList = response.data;
    },
    async dispatchGetOne(id: number): Promise<CsvParserPublic> {
      const response = await API.csvParser.getOne(id);
      return response.data;
    },
    async dispatchCreate(payload: CsvParserCreate): Promise<CsvParserPublic> {
      const response = await API.csvParser.create(payload);
      return response.data;
    },
    async dispatchUpdate(id: number, payload: CsvParserUpdate): Promise<CsvParserPublic> {
      const response = await API.csvParser.update(id, payload);
      return response.data;
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.csvParser.deleteOne(id);
    },
    async dispatchUpdateTimestampColumn(
      id: number,
      payload: CsvParserTimestampColumnUpdate,
    ): Promise<CsvParserTimestampColumnPublic> {
      const response = await API.csvParser.updateTimestampColumn(id, payload);
      return response.data;
    },
    async dispatchDeleteTimestampColumn(id: number): Promise<void> {
      await API.csvParser.deleteTimestampColumn(id);
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useCsvParserStore, import.meta.hot));
}
