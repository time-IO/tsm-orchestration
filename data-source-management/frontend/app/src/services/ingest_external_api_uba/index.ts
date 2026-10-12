import type {
  IngestExternalApiUbaPublic,
  IngestExternalApiUbaCreate,
  IngestExternalApiUbaUpdate,
} from '@/services/ingest_external_api_uba/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-api/uba/';

export default createIngestApiService<
  IngestExternalApiUbaPublic,
  IngestExternalApiUbaCreate,
  IngestExternalApiUbaUpdate
>(apiPath);
