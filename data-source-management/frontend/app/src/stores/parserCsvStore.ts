import { acceptHMRUpdate } from 'pinia';
import type {
  CsvParserCreate,
  CsvParserPublic,
  CsvParserUpdate,
} from 'src/services/parser_csv/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useCsvParserStore = createIngestStore<
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate
>('csvParserStore', API.csvParser);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useCsvParserStore, import.meta.hot));
}
