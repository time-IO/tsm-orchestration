import type {
  SoilcanParserPublic,
  SoilcanParserCreate,
  SoilcanParserUpdate,
} from '@/services/parser_soilcan/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'parser/soilcan/';

export default createIngestApiService<
  SoilcanParserPublic,
  SoilcanParserCreate,
  SoilcanParserUpdate
>(apiPath);
