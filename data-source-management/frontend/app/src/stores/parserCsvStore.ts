import { acceptHMRUpdate } from 'pinia';
import type {
  CsvParserCreate, CsvParserParse,
  CsvParserPublic,
  CsvParserUpdate,
} from 'src/services/parser_csv/types';
import { API } from 'src/services';
import {createParserStore} from "stores/factoryParserStore";

export const useCsvParserStore = createParserStore<
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
  CsvParserParse
>('csvParserStore', API.csvParser);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useCsvParserStore, import.meta.hot));
}
