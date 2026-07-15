import type {
  IngestExternalApiUbaPublic,
  IngestExternalApiUbaCreate,
  IngestExternalApiUbaUpdate,
} from 'src/services/ingest_external_api_uba/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/external-api/uba/';

export default createIngestApiService<
  IngestExternalApiUbaPublic,
  IngestExternalApiUbaCreate,
  IngestExternalApiUbaUpdate
>(apiPath);
