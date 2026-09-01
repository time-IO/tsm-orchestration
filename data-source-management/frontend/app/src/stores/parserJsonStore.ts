import { acceptHMRUpdate } from 'pinia';
import type {
  JsonParserCreate, JsonParserParse,
  JsonParserPublic,
  JsonParserUpdate,
} from 'src/services/parser_json/types';
import { API } from 'src/services';
import {createParserStore} from "stores/factoryParserStore";

export const useJsonParserStore = createParserStore<
  JsonParserPublic,
  JsonParserCreate,
  JsonParserUpdate,
  JsonParserParse
>('jsonParserStore', API.jsonParser);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useJsonParserStore, import.meta.hot));
}
