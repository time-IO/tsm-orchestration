import type {
  SoilcanParserPublic,
  SoilcanParserCreate,
  SoilcanParserUpdate,
} from 'src/services/parser_soilcan/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'parser/soilcan/';

export default createIngestApiService<
  SoilcanParserPublic,
  SoilcanParserCreate,
  SoilcanParserUpdate
>(apiPath);
