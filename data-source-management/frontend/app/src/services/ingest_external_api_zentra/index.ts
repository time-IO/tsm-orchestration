import type {
  IngestExternalApiZentraPublic,
  IngestExternalApiZentraCreate,
  IngestExternalApiZentraUpdate,
} from '@/services/ingest_external_api_zentra/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-api/zentra/';

export default createIngestApiService<
  IngestExternalApiZentraPublic,
  IngestExternalApiZentraCreate,
  IngestExternalApiZentraUpdate
>(apiPath);
