import type {
  JsonParserPublic,
  JsonParserCreate,
  JsonParserUpdate,
} from 'src/services/parser_json/types';
import {createParserApiService} from "src/services/factoryParserService";

const apiPath = 'parser/json/';

export default createParserApiService<JsonParserPublic, JsonParserCreate, JsonParserUpdate>(
  apiPath,
);
