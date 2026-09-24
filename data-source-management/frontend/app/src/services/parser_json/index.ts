import type {
  JsonParserPublic,
  JsonParserCreate,
  JsonParserUpdate,
  JsonParserValidate,
} from '@/services/parser_json/types';
import { createParserApiService } from '@/services/factoryParserService';

const apiPath = 'parser/json/';

export default createParserApiService<
  JsonParserPublic,
  JsonParserCreate,
  JsonParserUpdate,
  JsonParserValidate
>(apiPath);
