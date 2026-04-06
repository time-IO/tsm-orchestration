import type {
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
} from 'src/services/parser_csv/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'parser/csv/';

export default createIngestApiService<CsvParserPublic, CsvParserCreate, CsvParserUpdate>(apiPath);
