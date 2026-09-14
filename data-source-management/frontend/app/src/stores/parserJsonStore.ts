import { acceptHMRUpdate } from 'pinia';
import type {
  JsonParserCreate,
  JsonParserValidate,
  JsonParserPublic,
  JsonParserUpdate,
} from '@/services/parser_json/types';
import { API } from '@/services';
import { createParserStore } from 'stores/factoryParserStore';

export const useJsonParserStore = createParserStore<
  JsonParserPublic,
  JsonParserCreate,
  JsonParserUpdate,
  JsonParserValidate
>('jsonParserStore', API.jsonParser);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useJsonParserStore, import.meta.hot));
}
