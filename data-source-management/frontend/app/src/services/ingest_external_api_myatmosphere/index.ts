import type {
  IngestExternalApiMyAtmospherePublic,
  IngestExternalApiMyAtmosphereCreate,
  IngestExternalApiMyAtmosphereUpdate,
} from '@/services/ingest_external_api_myatmosphere/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-api/myatmosphere/';

export default createIngestApiService<
  IngestExternalApiMyAtmospherePublic,
  IngestExternalApiMyAtmosphereCreate,
  IngestExternalApiMyAtmosphereUpdate
>(apiPath);
