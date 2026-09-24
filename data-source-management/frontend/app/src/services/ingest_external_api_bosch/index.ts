import type {
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschUpdate,
} from '@/services/ingest_external_api_bosch/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-api/bosch/';

export default createIngestApiService<
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschUpdate
>(apiPath);
