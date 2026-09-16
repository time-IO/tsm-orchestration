import type {
  IngestExternalApiSensotoPublic,
  IngestExternalApiSensotoCreate,
  IngestExternalApiSensotoUpdate,
} from '@/services/ingest_external_api_sensoto/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-api/sensoto/';

export default createIngestApiService<
  IngestExternalApiSensotoPublic,
  IngestExternalApiSensotoCreate,
  IngestExternalApiSensotoUpdate
>(apiPath);
