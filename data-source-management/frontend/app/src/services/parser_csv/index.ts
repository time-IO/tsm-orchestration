import type {
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
  CsvParserValidate,
} from 'src/services/parser_csv/types';
import { createParserApiService } from 'src/services/factoryParserService';

const apiPath = 'parser/csv/';

export default createParserApiService<
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
  CsvParserValidate
>(apiPath);
