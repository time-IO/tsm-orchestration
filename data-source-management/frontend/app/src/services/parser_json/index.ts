import type {
  JsonParserPublic,
  JsonParserCreate,
  JsonParserUpdate,
} from 'src/services/parser_json/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'parser/json/';

export default createIngestApiService<JsonParserPublic, JsonParserCreate, JsonParserUpdate>(
  apiPath,
);
