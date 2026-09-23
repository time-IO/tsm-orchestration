import type {
  IngestHttpPublic,
  IngestHttpCreate,
  IngestHttpUpdate,
} from '@/services/ingest_http/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/http/';

export default createIngestApiService<IngestHttpPublic, IngestHttpCreate, IngestHttpUpdate>(
  apiPath,
);
