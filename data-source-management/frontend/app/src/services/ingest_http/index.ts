import type {
  IngestHttpPublic,
  IngestHttpCreate,
  IngestHttpUpdate,
} from 'src/services/ingest_http/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/http/';

export default createIngestApiService<
  IngestHttpPublic,
  IngestHttpCreate,
  IngestHttpUpdate
>(apiPath);


