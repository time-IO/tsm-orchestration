import type {
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
  CsvParserValidate,
} from '@/services/parser_csv/types';
import { createParserApiService } from '@/services/factoryParserService';

const apiPath = 'parser/csv/';

export default createParserApiService<
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
  CsvParserValidate
>(apiPath);
