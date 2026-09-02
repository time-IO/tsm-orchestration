import { acceptHMRUpdate } from 'pinia';
import type {
  JsonParserCreate,
  JsonParserPublic,
  JsonParserUpdate,
} from 'src/services/parser_json/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useJsonParserStore = createIngestStore<
  JsonParserPublic,
  JsonParserCreate,
  JsonParserUpdate
>('jsonParserStore', API.jsonParser);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useJsonParserStore, import.meta.hot));
}
